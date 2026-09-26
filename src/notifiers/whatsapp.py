"""WhatsApp notification dispatcher via CallMeBot API."""

import logging
import requests
from .base import BaseNotifier

logger = logging.getLogger(__name__)

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"


class WhatsAppNotifier(BaseNotifier):
    """Sends WhatsApp alerts using the free CallMeBot gateway."""

    def __init__(self, phone: str, api_key: str):
        # Ensure phone number has no leading '+' or spaces
        self.phone = phone.strip().lstrip("+").replace(" ", "")
        self.api_key = api_key.strip()

    def is_configured(self) -> bool:
        """Check if required credentials are present."""
        return bool(self.phone and self.api_key)

    def send(self, subject: str, message: str) -> bool:
        """
        Send WhatsApp message via CallMeBot.
        Subject is ignored as WhatsApp messages only have a message body.
        """
        if not self.is_configured():
            logger.error("WhatsApp notification failed: CALLMEBOT_PHONE or CALLMEBOT_API_KEY is not configured.")
            return False

        logger.info(f"Sending WhatsApp notification via CallMeBot to {self.phone[:4]}****...")

        params = {
            "phone": self.phone,
            "text": message,
            "apikey": self.api_key,
        }

        try:
            response = requests.get(CALLMEBOT_URL, params=params, timeout=25)
            if response.status_code == 200:
                logger.info("WhatsApp notification sent successfully!")
                return True
            else:
                logger.error(
                    f"CallMeBot API returned HTTP {response.status_code}: {response.text[:200]}"
                )
                return False
        except requests.RequestException as e:
            logger.error(f"Network error while sending WhatsApp message: {e}")
            return False
