# --------------------------------------------------
# Import required PyFlink libraries
# --------------------------------------------------

# Core streaming environment
from pyflink.datastream import StreamExecutionEnvironment

# State backend used to store operator state in memory
from pyflink.datastream.state_backend import HashMapStateBackend

# Checkpoint storage location
from pyflink.datastream.checkpoint_storage import FileSystemCheckpointStorage

# Table API environments
from pyflink.table import StreamTableEnvironment, EnvironmentSettings


# --------------------------------------------------
# Create Streaming Execution Environment
# --------------------------------------------------

# This is the main Flink runtime environment where the streaming job runs
env = StreamExecutionEnvironment.get_execution_environment()

# Set number of parallel processing slots
# Increasing parallelism improves throughput
env.set_parallelism(1)

# Enable fault tolerance by creating checkpoints every 30 seconds
# Checkpoints allow Flink to recover state after failures
env.enable_checkpointing(30000)


# --------------------------------------------------
# Configure Checkpointing Behavior
# --------------------------------------------------

# Get checkpoint configuration object
checkpoint_config = env.get_checkpoint_config()

# Use HashMapStateBackend
# Stores state in JVM heap (good for small projects / demos)
env.set_state_backend(HashMapStateBackend())

# Configure where checkpoint files are stored
# In production this would be S3 / HDFS / cloud storage
checkpoint_config.set_checkpoint_storage(
    FileSystemCheckpointStorage("file:///tmp/flink-checkpoints")
)

# Minimum delay between checkpoints
# Prevents constant checkpointing
checkpoint_config.set_min_pause_between_checkpoints(10000)

# Maximum time a checkpoint can take before failing
checkpoint_config.set_checkpoint_timeout(60000)

# Allow only one checkpoint running at a time
checkpoint_config.set_max_concurrent_checkpoints(1)


# --------------------------------------------------
# Create Table Environment
# --------------------------------------------------

# Table API allows SQL queries on streaming data
settings = EnvironmentSettings.in_streaming_mode()

# Bind Table API with the streaming environment
t_env = StreamTableEnvironment.create(env, environment_settings=settings)


# --------------------------------------------------
# Kafka Source Table
# --------------------------------------------------

# This defines a Flink Table connected to a Kafka topic
# Kafka topic contains incoming payment events

t_env.execute_sql("""
CREATE TABLE payments (
    payment_id STRING,
    bank_code STRING,
    amount DOUBLE,
    payment_type STRING,
    status STRING,
    event_time TIMESTAMP(3),

    -- Watermark allows event-time processing
    -- Late events within 5 seconds will still be processed
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',

    -- Kafka topic where raw payments arrive
    'topic' = 'payments.raw',

    -- Kafka broker inside docker network
    'properties.bootstrap.servers' = 'kafka:9092',

    -- Consumer group id
    'properties.group.id' = 'flink-payment-group',

    -- Start reading from earliest message
    'scan.startup.mode' = 'earliest-offset',

    -- Messages are JSON formatted
    'format' = 'json',

    -- Ignore malformed messages
    'json.ignore-parse-errors' = 'true',

    -- Timestamp format used by JSON events
    'json.timestamp-format.standard' = 'ISO-8601'
)
""")


# --------------------------------------------------
# PostgreSQL Sink Table
# --------------------------------------------------

# This table writes aggregated results into PostgreSQL
# Used later for dashboards (Grafana)

t_env.execute_sql("""
CREATE TABLE postgres_sink (
    bank_code STRING,
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    total_amount DOUBLE,
    success_count BIGINT,
    failed_count BIGINT
) WITH (
    'connector' = 'jdbc',

    -- PostgreSQL database connection
    'url' = 'jdbc:postgresql://postgres:5432/payments',

    -- Target table
    'table-name' = 'payment_metrics',

    -- Database credentials
    'username' = 'postgres',
    'password' = 'postgres',

    -- JDBC driver
    'driver' = 'org.postgresql.Driver'
)
""")


# --------------------------------------------------
# Kafka Alerts Sink Table
# --------------------------------------------------

# This Kafka topic receives alerts when failure rate exceeds threshold

t_env.execute_sql("""
CREATE TABLE alerts_sink (
    bank_code STRING,
    window_end TIMESTAMP(3),
    failure_rate DOUBLE
) WITH (
    'connector' = 'kafka',

    -- Kafka topic where alerts are sent
    'topic' = 'payments.alerts',

    'properties.bootstrap.servers' = 'kafka:9092',

    -- Alerts are JSON messages
    'format' = 'json'
)
""")


# --------------------------------------------------
# Create Aggregation View
# --------------------------------------------------

# This query performs windowed aggregation
# Every 10 seconds it calculates metrics per bank

t_env.execute_sql("""
CREATE VIEW payment_aggregates AS
SELECT
    bank_code,
    window_start,
    window_end,

    -- Total payment value
    SUM(amount) AS total_amount,

    -- Count successful payments
    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,

    -- Count failed payments
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) AS failed_count

FROM TABLE(
    TUMBLE(
        TABLE payments,

        -- Use event time instead of processing time
        DESCRIPTOR(event_time),

        -- Create 10 second tumbling windows
        INTERVAL '10' SECOND
    )
)

GROUP BY
    bank_code,
    window_start,
    window_end
""")


# --------------------------------------------------
# Execute Multiple Sinks in a Single Flink Job
# --------------------------------------------------

# StatementSet allows writing to multiple sinks
# while executing a single Flink pipeline

stmt_set = t_env.create_statement_set()


# --------------------------------------------------
# Sink 1: Write Aggregated Metrics to PostgreSQL
# --------------------------------------------------

stmt_set.add_insert_sql("""
INSERT INTO postgres_sink
SELECT *
FROM payment_aggregates
""")


# --------------------------------------------------
# Debug Sink (Console Output)
# --------------------------------------------------

# Useful for debugging
# Prints results in Flink container logs

t_env.execute_sql("""
CREATE TABLE debug_sink (
    bank_code STRING,
    window_end TIMESTAMP(3),
    success_count BIGINT,
    failed_count BIGINT,
    failure_rate DOUBLE
) WITH (
    'connector' = 'print'
)
""")


# Print aggregation results for debugging

stmt_set.add_insert_sql("""
INSERT INTO debug_sink
SELECT
    bank_code,
    window_end,
    success_count,
    failed_count,

    -- Calculate failure rate
    failed_count * 1.0 / NULLIF((failed_count + success_count),0) AS failure_rate

FROM payment_aggregates
""")


# --------------------------------------------------
# Sink 2: Send Alerts to Kafka
# --------------------------------------------------

# Only emit alerts if failure rate exceeds 5%

stmt_set.add_insert_sql("""
INSERT INTO alerts_sink
SELECT
    bank_code,
    window_end,

    -- Compute failure rate
    failed_count * 1.0 / NULLIF((failed_count + success_count), 0) AS failure_rate

FROM payment_aggregates

WHERE
    (failed_count + success_count) > 0
    AND failed_count * 1.0 / (failed_count + success_count) > 0.05
""")


# --------------------------------------------------
# Execute the Flink Streaming Job
# --------------------------------------------------

# All sinks will run as a single pipeline

stmt_set.execute()