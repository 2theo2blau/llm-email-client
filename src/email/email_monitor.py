# email_monitor.py
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import os
from typing import Dict, List, Optional
import psycopg2
from dataclasses import dataclass
import time

@dataclass
class EmailMessage:
    message_id: str
    sender: str
    recipient: str
    subject: str
    body: str
    timestamp: datetime
    raw_email: str

class EmailMonitor:
    def __init__(self, 
                 imap_server: str,
                 imap_port: int,
                 email: str,
                 email_password: str,
                 db_connection):
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.email = email
        self.email_password = email_password
        self.db = db_connection
        self.mail = None
    
    def connect(self) -> None:
        """Establish connection to IMAP server"""
        try:
            self.mail = imaplib.IMAP4(self.imap_server, self.imap_port, timeout=10)

            email = self.email.strip("'\"")
            email_password = self.email_password.strip("'\"")

            self.mail.login(self.email, self.email_password)
        
            status, messages = self.mail.select('INBOX')
            if status != 'OK':
                raise imaplib.IMAP4.error(f"Failed to select INBOX: {messages[0].decode()}")
        
        except imaplib.IMAP4.error as e:
            print(f"IMAP authentication failed: {e}")
            raise
        except ConnectionRefusedError as e:
            print(f"Connection refused by {self.imap_server}: {e}")
            raise
        except TimeoutError as e:
            print(f"Connection timeout to {self.imap_server}: {e}")
            raise
        except Exception as e:
            print(f"Error connecting to IMAP server: {e}")
            raise

    def parse_email_message(self, email_data: bytes) -> EmailMessage:
        email_message = email.message_from_bytes(email_data)

        # extract headers
        message_id = email_message.get('Message-ID', '')
        sender = email_message.get('From', '')
        recipient = email_message.get('To', '')
        subject = decode_header(email_message.get('Subject', ''))[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()

        # extract body
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = email_message.get_payload(decode=True).decode()
        
        # extract timestamp
        date_str = email_message.get('Date')
        timestamp = email.utils.parsedate_to_datetime(date_str)

        return EmailMessage(
            message_id=message_id,
            sender=sender,
            recipient=recipient,
            subject=subject,
            body=body,
            timestamp=timestamp,
            raw_email=str(email_message)
        )
    
    def store_email(self, email_message: EmailMessage) -> None:
        """Store email in database"""
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO emails
                (message_id, sender, recipient, subject, body, timestamp, raw_email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id) DO NOTHING
                """, 
                (
                    email_message.message_id,
                    email_message.sender,
                    email_message.recipient,
                    email_message.subject,
                    email_message.body,
                    email_message.timestamp,
                    email_message.raw_email
                )
            )
        self.db.commit()

    def check_new_emails(self) -> None:
        """Check for new emails in inbox"""
        try:
            self.mail.select('INBOX')
            _, messages = self.mail.search(None, 'UNSEEN')

            for msg_num in messages[0].split():
                _, msg_data = self.mail.fetch(msg_num, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = self.parse_email_message(email_body)
                self.store_email(email_message)

        except Exception as e:
            print(f"Error checking new emails: {e}")
            self.connect()

    def run(self, check_interval: int = 30) -> None:
        while True:
            try:
                self.check_new_emails()
                time.sleep(check_interval)
            except KeyboardInterrupt:
                print("Shutting down email monitor...")
                break
            except Exception as e:
                print(f"Error in email monitor: {e}")
                time.sleep(check_interval)

        