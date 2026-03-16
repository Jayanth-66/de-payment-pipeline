import json
import time
import random
from faker import Faker
from kafka import KafkaProducer
from datetime import datetime

# ---------------------------------------------------------
# Initialize Faker
# ---------------------------------------------------------
# Faker generates realistic fake data like UUIDs, names, etc.
fake = Faker()


# ---------------------------------------------------------
# Kafka Producer Configuration
# ---------------------------------------------------------
# KafkaProducer is responsible for sending messages to Kafka topics
producer = KafkaProducer(

    # Address of Kafka broker running in Docker
    bootstrap_servers='kafka:9092',

    # Convert Python dictionary → JSON → bytes
    # Kafka requires messages in bytes format
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),

    # Reliability settings
    # acks='all' ensures message is written safely
    acks='all',

    # Retry sending if broker temporarily fails
    retries=5,

    # Wait 5ms before sending batch (improves batching)
    linger_ms=5,

    # Batch size for sending messages efficiently
    batch_size=16384
)


# ---------------------------------------------------------
# Available Banks
# ---------------------------------------------------------
# These simulate which bank processed the payment
banks = ["HDFC", "ICICI", "SBI", "AXIS"]


# ---------------------------------------------------------
# Function to generate fake payment event
# ---------------------------------------------------------
def generate_payment():

    return {

        # Unique identifier for each payment
        "payment_id": fake.uuid4(),

        # Bank responsible for processing payment
        "bank_code": random.choice(banks),

        # Random payment amount
        "amount": round(random.uniform(100, 50000), 2),

        # Payment type simulation
        "payment_type": random.choice(["NEFT", "IMPS", "RTGS"]),

        # Simulate failures (~5% failure rate)
        "status": random.choices(
            ["SUCCESS", "FAILED"],
            weights=[95, 5]
        )[0],

        # Currency used
        "currency": "INR",

        # Event timestamp
        # Used by Flink for event-time processing
        "event_time": datetime.utcnow().isoformat(timespec="milliseconds"),
    }


print("Starting Payment Producer...")


# ---------------------------------------------------------
# Run producer for limited time (Airflow friendly)
# ---------------------------------------------------------
# Airflow tasks must finish eventually.
# So instead of infinite loop we run for 60 seconds.
RUN_DURATION = 60
EVENT_DELAY = 0.01  # Delay between events (100 events/sec)

# Record when producer started
start_time = time.time()
print("Starting payment producer...")

# ---------------------------------------------------------
# Generate and send payment events
# ---------------------------------------------------------
while time.time() - start_time < RUN_DURATION:

    # Generate a fake payment event
    payment = generate_payment()

    # Send message to Kafka topic
    producer.send(
        "payments.raw",                      # Kafka topic name
        key=payment["bank_code"].encode("utf-8"),  # Partition by bank
        value=payment
    )

    # Print message for debugging
    print("Sent:", payment)

    # Control throughput (events per second)
    time.sleep(EVENT_DELAY)


# ---------------------------------------------------------
# Ensure all messages are delivered
# ---------------------------------------------------------
producer.flush()

print("Finished producing events.")