CREATE TABLE produce_messages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    count INTEGER NOT NULL,
    amount FLOAT NOT NULL
);