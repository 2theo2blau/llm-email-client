# main.py

import os
import psycopg2
from src.email.email_monitor import EmailMonitor
from src.email.email_sender import EmailSender
from src.processing.response_processing import EmailProcessor
from src.llm.llm_processing import LLMProcessor
from dotenv import load_dotenv
import time
import threading

def main():
    load_dotenv(override=True)

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

    sender = EmailSender(
        db_connection=db_connection,
        smtp_server=os.getenv("SMTP_SERVER"),
        smtp_port=os.getenv("SMTP_PORT"),
        email=os.getenv("EMAIL"),
        email_password=os.getenv("EMAIL_PASSWORD")
    )

    llm_processor = LLMProcessor(
        db_connection=db_connection,
        api_base_url=os.getenv("LLM_API_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("API_MODEL"),
        agent_id=os.getenv("AGENT_ID")
    )

    response_processor = EmailProcessor(
        db_connection=db_connection,
        llm_processor=llm_processor,
        email_sender=sender,
        batch_size=4
    )
   
    try:
        monitor.connect()
        print("Email monitor connected")

        monitor_thread = threading.Thread(target=monitor.run, name="EmailMonitor")
        response_thread = threading.Thread(target=response_processor.run, name="EmailSender")

        monitor_thread.start()
        response_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
            

        monitor_thread.join()
        response_thread.join()

    except Exception as e:
        print(f"Error in main: {e}")

    finally:
        if db_connection:
            db_connection.close()
            print("database connection closed")

if __name__ == "__main__":
    main()