from dataclasses import dataclass
import smtplib
from typing import List, Optional
from datetime import datetime
import requests
import os
import time
from src.email.email_monitor import EmailMessage
from dotenv import load_dotenv

@dataclass
class UnprocessedEmail:
    id: int
    message_id: str
    sender: str
    subject: str
    body: str
    timestamp: datetime

@dataclass
class LLMResponse:
    original_email_id: int
    response_subject: str
    response_body: str
    generated_at: datetime
    model_used: str
    sent_at: datetime

class EmailProcessor:
    def __init__(self,
                 db_connection,
                 api_base_url: str,
                 api_key: str,
                 model: str,
                 agent_id: str,
                 smtp_server: str,
                 smtp_port: int,
                 email: str,
                 email_password: str,
                 batch_size: int = 4,):
        self.db = db_connection
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.model = model
        self.agent_id = agent_id
        self.batch_size = batch_size

        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.email_password = email_password

    def get_unprocessed_emails(self) -> List[UnprocessedEmail]:
        """Fetch new or unprocessed emails from the database"""
        with self.db.cursor() as cur:
            cur.execute("""
            SELECT id, message_id, sender, subject, body, timestamp
            FROM emails
            WHERE processed = FALSE AND response_id IS NULL
            LIMIT %s
            """, (self.batch_size,))

            emails = []
            for row in cur.fetchall():
                emails.append(UnprocessedEmail(
                    id=row[0],
                    message_id=row[1],
                    sender=row[2],
                    subject=row[3],
                    body=row[4],
                    timestamp=row[5]
                ))
            return emails
        
    def create_prompt(self, email: UnprocessedEmail) -> str:
        """Expand stored email elements into a prompt for the LLM"""
        return f"""
        Email:
        From: {email.sender}
        Subject: {email.subject}
        Timestamp: {email.timestamp}

        Message Body:
        {email.body}

        Please write a thorough and articulate response to the email above.
        """
    
    def query_llm(self, prompt: str) -> str:
        """Send request to the LLM API and return the response"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            # "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            # "temperature": 1.0,
            "agent_id": self.agent_id,
        }

        response = requests.post(
            f"{self.api_base_url}/v1/agents/completions",
            headers=headers,
            json=data
        )

        if response.status_code != 200:
            raise Exception(f"API Request Failed: {response.text}")

        return response.json()["choices"][0]["message"]["content"]

    def store_response(self, response: LLMResponse) -> int:
        """Store the generated response in the database"""
        with self.db.cursor() as cur:
            cur.execute("""
            INSERT INTO responses
            (original_email_id, response_subject, response_body, generated_at, model_used, sent_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """, (
            response.original_email_id,
            response.response_subject,
            response.response_body,
            response.generated_at,
            response.model_used,
            response.sent_at,
            ))
            response_id = cur.fetchone()[0]

            # mark original email as processed
            cur.execute("""
            UPDATE emails
            SET PROCESSED = TRUE, response_id = %s
            WHERE id = %s
            """, (response_id, response.original_email_id))

            self.db.commit()
            return response_id
        
    def process_emails(self) -> None:
        """Process batch of unprocessed emails"""
        emails = self.get_unprocessed_emails()

        for email in emails:
            try:
                prompt = self.create_prompt(email)
                response_body = self.query_llm(prompt)
                response_subject = f"Re: {email.subject}" if not email.subject.startswith("Re:") else email.subject

                response = LLMResponse(
                    original_email_id=email.id,
                    response_body=response_body,
                    response_subject=response_subject,
                    model_used="mistral-agent",
                    generated_at=datetime.now(),
                    sent_at=None
                )

                self.store_response(response)

            except Exception as e:
                print(f"Error processing email {email.id}: {e}")
                self.db.rollback()
                continue

            # add delay between requests
            # time.sleep(1)

    def send_responses(self, response_id: int) -> None:
        """Send the response using SMTP"""
        with self.db.cursor() as cur:
            cur.execute("""
            SELECT r.id, r.response_subject, r.response_body, r.original_email_id, e.message_id, e.sender, e.subject
            FROM responses r
            JOIN emails e ON e.id = r.original_email_id
            WHERE r.id = %s AND r.sent = FALSE
            """, (response_id,))

            result = cur.fetchone()
            if not result:
                print(f"Response {response_id} not found")
                return

            _, response_subject,response_body, original_email_id, message_id, sender, original_subject = result

            # create response email
            email_message = EmailMessage()
            email_message["From"] = self.email
            email_message["To"] = sender
            email_message["Subject"] = response_subject
            email_message["In-Reply-To"] = message_id
            email_message["References"] = message_id
            email_message.set_content(response_body)

            try:
                with smtplib.SMTP(self.email, self.smtp_port) as smtp_server:
                    smtp_server.login(self.email, self.email_password)
                    smtp_server.send_message(email_message)
                    print(f"Response {response_id} sent to {sender}")

                cur.execute("""
                    UPDATE responses
                    SET sent = TRUE, sent_at = %s
                    WHERE id = %s
                """, (datetime.now(), response_id))
                self.db.commit()
                print(f"Response {response_id} updated as sent in database")

            except Exception as e:
                print(f"Error sending response {response_id}: {e}")
                self.db.rollback()

    def run(self, check_interval: int = 10) -> None:
        print(f"[{datetime.now()}] Starting email processor")

        while True:
            try:
                print(f"[{datetime.now()}] Processing new emails")
                self.process_emails()
                
                with self.db.cursor() as cur:
                    cur.execute("""
                        SELECT id FROM responses
                        WHERE sent = FALSE
                        ORDER BY generated_at ASC
                    """)
                    unsent_responses = cur.fetchall()

                    for (response_id,) in unsent_responses:
                        print(f"[{datetime.now()}] Sending response {response_id}")
                        self.send_responses(response_id)

                    time.sleep(check_interval)

            except Exception as e:
                print(f"Error in email processor: {e}")
                time.sleep(check_interval)