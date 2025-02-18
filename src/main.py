# main.py

import os
import psycopg2
from src.email.email_monitor import EmailMonitor
from src.processing.processing import EmailProcessor
from dotenv import load_dotenv
import time

def run_email_processor(db_connection, check_interval: int = 30):
    processor = EmailProcessor(
        db_connection=db_connection,
        api_base_url=os.getenv("LLM_API_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("API_MODEL"),
        smtp_server=os.getenv("SMTP_SERVER"),
        smtp_port=os.getenv("SMTP_PORT"),
        email=os.getenv("EMAIL"),
        email_password=os.getenv("EMAIL_PASSWORD")
    )

    while True:
        try:
            processor.process_emails()
            time.sleep(check_interval)
        except Exception as e:
            

def main():
    load_dotenv()

    # Initialize postgres DB connection
    db_connection = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

    # Initialize email monitor
    monitor = EmailMonitor(
        imap_server=os.getenv("IMAP_SERVER"),
        imap_port=os.getenv("IMAP_PORT"),
        email=os.getenv("EMAIL"),
        email_password=os.getenv("EMAIL_PASSWORD"),
        db_connection=db_connection
    )

    try:
        monitor.connect()
        monitor.run()
    finally:
        db_connection.close()

if __name__ == "__main__":
    main()