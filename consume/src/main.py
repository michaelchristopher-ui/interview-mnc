from fastapi import FastAPI, HTTPException
from kafka import KafkaConsumer
import json
import psycopg2
import uvicorn
import os

import threading
import time
import signal
import asyncio
from contextlib import asynccontextmanager

app = FastAPI()

# Global variables for thread management
consumer_thread = None
shutdown_event = threading.Event()

# Instance configuration
INSTANCE_NAME = os.getenv('INSTANCE_NAME', 'consumer-instance-1')

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
KAFKA_TOPIC = 'servicea-topic'

# Database configuration
DB_NAME = os.getenv('DB_NAME', "postgres")
DB_USER = os.getenv('DB_USER', "postgres")
DB_PASSWORD = os.getenv('DB_PASSWORD', "postgres")
DB_HOST = os.getenv('DB_HOST', "localhost")
DB_PORT = os.getenv('DB_PORT', "5432")

def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def insert_message_to_db(name: str, count: int, amount: float):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO consumer.produce_messages (name, count, amount)
            VALUES (%s, %s, %s)
            """,
            (name, count, amount)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def kafka_consumer_worker():
    """Kafka consumer worker with proper shutdown handling"""
    consumer = None
    while not shutdown_event.is_set():
        try:
            print(f"Starting Kafka consumer {INSTANCE_NAME} with servers: {KAFKA_BOOTSTRAP_SERVERS}")
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='earliest',
                enable_auto_commit=False,  # Manual commit to ensure message processing
                group_id="consume-group",
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000
            )
            
            for msg in consumer:
                # Check for shutdown signal
                if shutdown_event.is_set():
                    print("Shutdown signal received, stopping message processing")
                    break
                    
                data = msg.value
                try:
                    insert_message_to_db(
                        name=data["Name"],
                        count=data["Count"],
                        amount=data["Amount"]
                    )
                    # Only commit if database insertion was successful
                    consumer.commit()
                    print(f"{INSTANCE_NAME} consumed message {json.dumps(data)}")
                except Exception as db_exc:
                    print(f"Failed to insert message to database: {db_exc}")
                    # Don't commit the message, it will be retried
                    continue
                    
        except Exception as e:
            if not shutdown_event.is_set():
                print(f"Kafka consumer error: {e}")
                time.sleep(5)  # Wait before retrying
        finally:
            if consumer:
                print("Closing Kafka consumer...")
                consumer.close()
                consumer = None
    
    print("Kafka consumer worker thread stopped")


# Use FastAPI lifespan for background thread management
@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_thread
    
    # Startup
    print("Starting Kafka consumer thread...")
    shutdown_event.clear()
    consumer_thread = threading.Thread(target=kafka_consumer_worker, daemon=False)  # Not daemon!
    consumer_thread.start()
    
    try:
        yield
    finally:
        # Shutdown
        print("Shutting down Kafka consumer...")
        shutdown_event.set()
        
        # Wait for thread to finish gracefully
        if consumer_thread and consumer_thread.is_alive():
            consumer_thread.join(timeout=10)  # Wait up to 10 seconds
            if consumer_thread.is_alive():
                print("Warning: Consumer thread did not shut down gracefully")
        
        print("Kafka consumer shutdown complete")

app = FastAPI(lifespan=lifespan)


@app.get("/status")
def status():
    return {"status": "Kafka consumer running in background", "instance": INSTANCE_NAME}

def main():
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

if __name__ == "__main__":
    main()