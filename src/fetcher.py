"""Fetcher for Danish electricity spot prices from Energi Data Service (Energinet)."""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo
import requests

logger = logging.getLogger(__name__)

API_URL = "https://api.energidataservice.dk/dataset/Elspotprices"
TIMEZONE = ZoneInfo("Europe/Copenhagen")


class ElectricityFetcher:
    def __init__(self, price_area: str = "DK2"):
        self.price_area = price_area.upper()

    def get_tomorrow_date(self) -> str:
        """Returns tomorrow's date string (YYYY-MM-DD) in Copenhagen local time."""
        now = datetime.now(TIMEZONE)
        tomorrow = now + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")

    def fetch_prices_for_date(self, target_date: Optional[str] = None, max_retries: int = 3) -> List[Dict]:
        """
        Fetch 24-hour spot prices for a given date (defaults to tomorrow).
        Returns a list of dicts with keys: hour, time_str, price_kwh, date, raw_mwh.
        """
        if not target_date:
            target_date = self.get_tomorrow_date()

        filter_json = json.dumps({"PriceArea": [self.price_area]})
        params = {
            "offset": 0,
            "start": f"{target_date}T00:00",
            "end": f"{target_date}T23:59",
            "filter": filter_json,
            "sort": "HourDK asc",
            "limit": 50,
        }
        headers = {"User-Agent": "ElectricityPriceNotifier/1.0"}

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching electricity prices for {target_date} ({self.price_area})...")
                response = requests.get(API_URL, params=params, headers=headers, timeout=15)

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 10))
                    logger.warning(
                        f"Rate limited (429). Retrying after {retry_after}s (attempt {attempt}/{max_retries})..."
                    )
                    if attempt < max_retries:
                        time.sleep(min(retry_after, 30))
                        continue
                    response.raise_for_status()

                response.raise_for_status()
                payload = response.json()
                records = payload.get("records", [])
                return self._parse_records(records, target_date)

            except requests.RequestException as e:
                logger.error(f"Error fetching electricity prices: {e}")
                if attempt < max_retries:
                    time.sleep(3 * attempt)
                    continue
                raise

        return []

    def _parse_records(self, records: List[Dict], target_date: str) -> List[Dict]:
        """Convert raw Energinet records to standardized hourly list."""
        parsed = []
        for r in records:
            # HourDK format: "2026-09-27T00:00:00"
            hour_str = r.get("HourDK", "")
            try:
                dt = datetime.fromisoformat(hour_str)
                hour = dt.hour
            except Exception:
                hour = 0

            # SpotPriceDKK is in DKK per MWh. Divide by 1000 for DKK per kWh.
            raw_mwh = r.get("SpotPriceDKK", 0.0)
            price_kwh = round(raw_mwh / 1000.0, 4)

            time_str = f"{hour:02d}:00 - {(hour + 1) % 24:02d}:00"
            if hour == 23:
                time_str = "23:00 - 00:00"

            parsed.append({
                "date": target_date,
                "hour": hour,
                "time_str": time_str,
                "price_kwh": price_kwh,
                "raw_mwh": raw_mwh,
                "price_eur_mwh": r.get("SpotPriceEUR", 0.0),
            })

        # Ensure sorted by hour ascending
        parsed.sort(key=lambda x: x["hour"])
        return parsed
