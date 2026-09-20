import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import asyncio
from typing import Optional

SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025")) # Default to MailHog or local test server
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@sanchayias.com")

def _send_email_sync(to_email: str, subject: str, body: str, html_body: Optional[str] = None):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email

    msg.attach(MIMEText(body, "plain"))
    if html_body:
        msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            if SMTP_USER and SMTP_PASS:
                server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"[Notifications] Email sent to {to_email}: {subject}")
    except Exception as e:
        print(f"[Notifications] Failed to send email to {to_email}: {e}")
        # In a real app we'd log this or queue it for retry. We'll fail silently here for resilience.

async def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None):
    """Asynchronously send an email so as not to block the API."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_email_sync, to_email, subject, body, html_body)

async def send_onboarding_email(client_email: str, client_name: str, advisor_name: str = "Your Advisor"):
    subject = f"Welcome to Sanchay IAS, {client_name}"
    body = f"Hello {client_name},\n\nWelcome to Sanchay IAS! {advisor_name} has successfully onboarded you to the platform.\nYou will soon receive your login credentials to access the Client Portal.\n\nBest,\nSanchay IAS Team"
    html_body = f"<p>Hello <strong>{client_name}</strong>,</p><p>Welcome to Sanchay IAS! <strong>{advisor_name}</strong> has successfully onboarded you to the platform.</p><p>You will soon receive your login credentials to access the Client Portal.</p><p>Best,<br>Sanchay IAS Team</p>"
    await send_email(client_email, subject, body, html_body)

async def send_task_notification(client_email: str, client_name: str, task_title: str):
    subject = f"New Action Required: {task_title}"
    body = f"Hello {client_name},\n\nA new task '{task_title}' has been assigned to your account. Please log in to your Client Portal to review and complete it.\n\nBest,\nSanchay IAS Team"
    html_body = f"<p>Hello <strong>{client_name}</strong>,</p><p>A new task <strong>'{task_title}'</strong> has been assigned to your account. Please log in to your Client Portal to review and complete it.</p><p>Best,<br>Sanchay IAS Team</p>"
    await send_email(client_email, subject, body, html_body)
