# Kafka Consumer Service

This service consumes messages from Kafka and stores them in a PostgreSQL database.

## Architecture

- **FastAPI**: Web framework for the consumer service
- **Kafka Consumer**: Consumes messages from the `servicea-topic`
- **PostgreSQL**: Database to store consumed messages
- **Docker**: Containerized deployment

## Prerequisites

1. Make sure the producer service is running (with Kafka) from the `../produce` directory
2. Docker and Docker Compose installed

## Database Schema

The service creates a `produce_messages` table with:
- `id`: Serial primary key
- `name`: Unique varchar(255)
- `count`: Integer
- `amount`: Float

## Running the Service

### Using Docker Compose

```bash
# Build and start the consumer service
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f fastapi-consumer

# Stop the service
docker-compose down
```

### Configuration

The service uses the following ports:
- **Consumer App**: `8002` (mapped to container port 8001)
- **Database**: `5433` (mapped to container port 5432)

Environment variables:
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address (default: `host.docker.internal:9092`)
- `DB_HOST`: Database host (default: `consume-db`)
- `DB_PORT`: Database port (default: `5432`)
- `DB_NAME`: Database name (default: `postgres`)
- `DB_USER`: Database user (default: `postgres`)
- `DB_PASSWORD`: Database password (default: `postgres`)

## API Endpoints

- `GET /status`: Returns the status of the Kafka consumer

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

The application will start on `http://localhost:8001`

### Testing

```bash
# Run tests
pytest tests/
```

## Notes

- The consumer runs in a background thread and continuously processes messages from Kafka
- Database connections are managed per operation
- The service includes automatic reconnection logic for Kafka failures
- Duplicate messages are handled with `ON CONFLICT (name) DO NOTHING`

## Project Structure
```
my-python-project
├── src
│   └── main.py
├── tests
│   └── test_main.py
├── requirements.txt
└── README.md
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd my-python-project
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application
To run the application, execute the following command:
```
python src/main.py
```

## Running Tests
To run the unit tests, use the following command:
```
python -m unittest discover -s tests
```

## License
This project is licensed under the MIT License. See the LICENSE file for more details.