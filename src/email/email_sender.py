import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

class EmailSender:
    def __init__(self,
                 smtp_server: str,
                 smtp_port: int,
                 email: str,
                 email_password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.email_password = email_password

        self.template_path = os.path.join(os.path.dirname(__file__), "../templates/email-template.html")

    def load_template(self) -> str:
        with open(self.template_path, "r") as file:
            return file.read()
        
    def insert_into_template(self, response_body: str) -> str:
        formatted_response = response_body.replace("\n", "<br>")
        template = self.load_template()
        template_response = template.replace("{response_body}", formatted_response)
        return template_response
    
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
            email_message = MIMEMultipart('alternative')
            email_message["From"] = self.email
            email_message["To"] = sender
            email_message["Subject"] = response_subject
            email_message["In-Reply-To"] = message_id
            email_message["References"] = message_id
            
            body_text = MIMEText(response_body, 'plain')
            
            html_body = self.insert_into_template(response_body)
            html_email = MIMEText(html_body, 'html')

            email_message.attach(body_text)
            email_message.attach(html_email)

            # email_message.set_content(response_body)

            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as smtp_server:
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