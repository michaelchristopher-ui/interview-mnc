from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from kafka import KafkaProducer
import json
import os
import uvicorn
import httpx

app = FastAPI()

# Authentication configuration
AUTH_SERVICE_BASE_URL = os.getenv('AUTH_SERVICE_BASE_URL', 'http://localhost:8001')
security = HTTPBearer()

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
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

# Authentication dependency
async def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validate bearer token by calling the authentication service
    """
    print(f"Received token: {credentials.credentials}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AUTH_SERVICE_BASE_URL}/validate",
                json={"token": credentials.credentials}
            )

            print(f"Auth service response status: {response.status_code}")
            print(f"Auth service response body: {response.json()}")

        if response.status_code == 200:
            validation_result = response.json()
            if validation_result.get("isValid", False):
                return credentials.credentials
        
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except httpx.RequestException:
        raise HTTPException(
            status_code=503,
            detail="Authentication service unavailable",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

@app.get("/health")
async def health_check():
    """
    Health check endpoint - no authentication required
    """
    return {"status": "healthy", "service": "kafka-producer"}

@app.post("/produce")
async def produce_message(
    msg: ProduceMessage, 
    token: str = Depends(validate_token)
):
    """
    Produce a message to Kafka. Requires valid bearer token.
    """
    try:
        producer.send(KAFKA_TOPIC, msg.dict())
        producer.flush()
        return {
            "status": "Message sent to Kafka",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kafka error: {str(e)}")

def main():
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()