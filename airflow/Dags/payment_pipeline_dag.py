from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    "owner": "data-engineer",
    "start_date": datetime(2024,1,1),
    "retries": 1
}

dag = DAG(
    "payment_streaming_pipeline",
    default_args=default_args,
    schedule_interval=None,
    catchup=False
)

# Start producer
start_producer = BashOperator(
    task_id="start_kafka_producer",
    bash_command="python /opt/airflow/dags/payment_producer.py",
    dag=dag
)

# Submit Flink job
submit_flink_job = BashOperator(
    task_id="submit_flink_job",
    bash_command="""
    docker exec flink-jobmanager flink run \
    -py /opt/flink/flink-job/PaymentStreamProcessor.py
    """,
    dag=dag
)

# Monitor checkpoint
monitor_checkpoint = BashOperator(
    task_id="monitor_flink_checkpoint",
    bash_command="curl http://flink-jobmanager:8081/jobs",
    dag=dag
)

# Validate postgres aggregates
validate_aggregates = BashOperator(
    task_id="validate_postgres_aggregates",
    bash_command="""
    docker exec postgres psql -U postgres -d payments \
    -c "SELECT COUNT(*) FROM payment_metrics;"
    """,
    dag=dag
)

# Refresh grafana
refresh_grafana = BashOperator(
    task_id="refresh_grafana",
    bash_command="curl http://grafana:3000",
    dag=dag
)

start_producer >> submit_flink_job >> monitor_checkpoint >> validate_aggregates >> refresh_grafana