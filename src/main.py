# main.py

import os
import psycopg2
from email.email_monitor import EmailMonitor
from dotenv import load_dotenv

def main():
    load_dotenv()

    # Initialize postgres DB connection
    db_conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

    # Initialize email monitor
    monitor = EmailMonitor(
        imap_server=os.getenv("IMAP_SERVER"),
        email_address=os.getenv("IMAP_USER"),
        email_password=os.getenv("IMAP_PASSWORD"),
        db_conn=db_conn
    )

    try:
        monitor.connect()
        monitor.run()
    finally:
        db_conn.close()

if __name__ == "__main__":
    main()