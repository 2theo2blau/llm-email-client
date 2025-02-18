CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    sender VARCHAR(255) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject TEXT,
    body TEXT,
    timestamp TIMESTAMP WITH TIME ZONE,
    raw_email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE,
    response_id INTEGER REFERENCES responses(id)
);

CREATE TABLE IF NOT EXISTS responses (
    id SERIAL PRIMARY KEY,
    original_email_id INTEGER REFERENCES emails(id),
    response_message_id VARCHAR(255),
    response_subject TEXT NOT NULL,
    response_body TEXT NOT NULL,
    model_used VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent BOOLEAN DEFAULT FALSE
)