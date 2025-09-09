CREATE TABLE consumer.produce_messages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    count INTEGER NOT NULL,
    amount FLOAT NOT NULL
);