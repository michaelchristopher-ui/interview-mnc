from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
import json

app = FastAPI()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'servicea-topic'

# Pydantic model for the request body
class ProduceMessage(BaseModel):
    Name: str
    Count: int
    Amount: float

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.post("/produce")
def produce_message(msg: ProduceMessage):
    try:
        producer.send(KAFKA_TOPIC, msg.dict())
        producer.flush()
        return {"status": "Message sent to Kafka"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kafka error: {str(e)}")

def main():
    import uvicorn
    uvicorn.run("ServiceA:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()