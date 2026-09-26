"""Configuration management for electricity price notifier."""

import os
# Attempt to load local .env file if dotenv is available, or manually parse if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Minimal fallback parser for local .env without external dependency
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("\"'"))

PRICE_AREA = os.getenv("PRICE_AREA", "DK2").upper()
CHEAP_THRESHOLD_DKK = float(os.getenv("CHEAP_THRESHOLD_DKK", "1.0"))
TOP_CHEAPEST_COUNT = int(os.getenv("TOP_CHEAPEST_COUNT", "3"))

# Tariff & all-inclusive price calculation
INCLUDE_TARIFFS = os.getenv("INCLUDE_TARIFFS", "true").lower() in ("true", "1", "yes")
GRID_OPERATOR = os.getenv("GRID_OPERATOR", "Radius").strip()

# CallMeBot WhatsApp settings
CALLMEBOT_PHONE = os.getenv("CALLMEBOT_PHONE", "").strip().lstrip("+")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY", "").strip()

# Active notifiers (e.g. "whatsapp", or "whatsapp,email")
NOTIFIERS_ENABLED = [
    n.strip().lower() for n in os.getenv("NOTIFIERS_ENABLED", "whatsapp").split(",") if n.strip()
]

# Email settings (optional / future expansion)
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_SMTP_USER = os.getenv("EMAIL_SMTP_USER", "")
EMAIL_SMTP_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")
