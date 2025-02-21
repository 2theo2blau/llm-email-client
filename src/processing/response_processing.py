from typing import List
from datetime import datetime
import time
import os
from src.models.email_models import UnprocessedEmail, LLMResponse
from src.llm.llm_processing import LLMProcessor
from src.email.email_sender import EmailSender

class EmailProcessor:
    def __init__(self,
                 db_connection,
                 llm_processor: LLMProcessor,
                 email_sender: EmailSender,
                 batch_size: int):
        self.db = db_connection
        self.llm_processor = llm_processor
        self.email_sender = email_sender
        self.batch_size = batch_size


    def get_unprocessed_emails(self) -> List[UnprocessedEmail]:
        """Fetch new or unprocessed emails from the database"""
        with self.db.cursor() as cur:
            cur.execute("""
            SELECT id, message_id, sender, subject, body, timestamp
            FROM emails
            WHERE processed = FALSE
            AND id NOT IN (SELECT original_email_id FROM responses)
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
            print(f"Response {response_id} stored in database")
            return response_id
        
    
    def process_emails(self) -> None:
        """Process batch of unprocessed emails"""
        emails = self.get_unprocessed_emails()
        print(f"Found {len(emails)} unprocessed emails")

        for email in emails:
            try:
                prompt = self.llm_processor.create_prompt(email)
                response_body = self.llm_processor.query_llm(prompt)
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
                        self.email_sender.send_responses(response_id)

                    time.sleep(check_interval)

            except Exception as e:
                print(f"Error in email processor: {e}")
                time.sleep(check_interval)