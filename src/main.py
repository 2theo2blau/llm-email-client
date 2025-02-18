# main.py

import os
import psycopg2
from src.email.email_monitor import EmailMonitor
from dotenv import load_dotenv

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