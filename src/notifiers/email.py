"""Email notification dispatcher via standard SMTP (e.g., Gmail, Outlook, or transactional mail)."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from .base import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """Sends email alerts via SMTP. Ready for when email notifications are enabled."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        to_email: str,
    ):
        self.smtp_host = smtp_host.strip()
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user.strip()
        self.smtp_password = smtp_password.strip()
        self.to_email = to_email.strip()

    def is_configured(self) -> bool:
        """Checks if all necessary email credentials are provided."""
        return bool(
            self.smtp_host
            and self.smtp_user
            and self.smtp_password
            and self.to_email
        )

    def send(self, subject: str, message: str) -> bool:
        if not self.is_configured():
            logger.warning("Email notification skipped: SMTP credentials not fully configured.")
            return False

        logger.info(f"Sending email notification to {self.to_email}...")
        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = self.to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info("Email notification sent successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
