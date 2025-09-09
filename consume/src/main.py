from fastapi import FastAPI, HTTPException
from kafka import KafkaConsumer
import json
import psycopg2
import uvicorn

import threading
import time
from contextlib import asynccontextmanager

app = FastAPI()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'servicea-topic'

# Database configuration
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

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
            INSERT INTO produce_messages (name, count, amount)
            VALUES (%s, %s, %s)
            ON CONFLICT (name) DO NOTHING
            """,
            (name, count, amount)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def kafka_consumer_worker():
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id="consume-group",
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000
            )
            for msg in consumer:
                data = msg.value
                try:
                    insert_message_to_db(
                        name=data["Name"],
                        count=data["Count"],
                        amount=data["Amount"]
                    )
                except Exception as db_exc:
                    pass
            consumer.close()
        except Exception as e:
            # Optionally log error
            time.sleep(5)  # Wait before retrying


# Use FastAPI lifespan for background thread management
@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=kafka_consumer_worker, daemon=True)
    thread.start()
    try:
        yield
    finally:
        # No explicit stop for the thread; add logic if needed
        pass

app = FastAPI(lifespan=lifespan)


@app.get("/status")
def status():
    return {"status": "Kafka consumer running in background"}

def main():
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

if __name__ == "__main__":
    main()