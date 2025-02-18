CREATE TABLE IF NOT EXISTS responses (
    id SERIAL PRIMARY KEY,
    original_email_id INTEGER,
    response_message_id VARCHAR(255),
    original_sender VARCHAR(255),
    response_subject TEXT NOT NULL,
    response_body TEXT NOT NULL,
    model_used VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    sent BOOLEAN DEFAULT FALSE
);

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

ALTER TABLE responses
ADD CONSTRAINT fk_original_email
FOREIGN KEY (original_email_id) REFERENCES emails(id);