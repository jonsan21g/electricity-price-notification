"""Fetcher for Danish electricity spot prices from Energi Data Service (Energinet)."""

from collections import defaultdict
from datetime import datetime, timedelta
import json
import logging
import time
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo
import requests

logger = logging.getLogger(__name__)

# Energinet transitioned to DayAheadPrices in late 2025 with 15-min intervals
API_URL = "https://api.energidataservice.dk/dataset/DayAheadPrices"
FALLBACK_API_URL = "https://api.energidataservice.dk/dataset/Elspotprices"
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
        Fetch spot prices for a given date (defaults to tomorrow) from Energi Data Service.
        Aggregates 15-minute intervals into 24 standard hourly periods.
        """
        if not target_date:
            target_date = self.get_tomorrow_date()

        filter_json = json.dumps({"PriceArea": [self.price_area]})
        params = {
            "offset": 0,
            "start": f"{target_date}T00:00",
            "end": f"{target_date}T23:59",
            "filter": filter_json,
            "sort": "TimeDK asc",
            "limit": 120,
        }
        headers = {"User-Agent": "ElectricityPriceNotifier/1.0"}

        # Try DayAheadPrices first, fallback to Elspotprices if needed
        urls_to_try = [API_URL, FALLBACK_API_URL]

        for url in urls_to_try:
            # Adjust sort parameter if using legacy dataset
            if "Elspotprices" in url:
                params["sort"] = "HourDK asc"

            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(f"Fetching electricity prices for {target_date} ({self.price_area}) from {url.split('/')[-1]}...")
                    response = requests.get(url, params=params, headers=headers, timeout=15)

                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 10))
                        logger.warning(
                            f"Rate limited (429). Retrying after {retry_after}s (attempt {attempt}/{max_retries})..."
                        )
                        if attempt < max_retries:
                            time.sleep(min(retry_after, 30))
                            continue
                        response.raise_for_status()

                    if response.status_code == 404:
                        logger.warning(f"Dataset {url.split('/')[-1]} returned 404, trying fallback...")
                        break

                    response.raise_for_status()
                    payload = response.json()
                    records = payload.get("records", [])

                    if records:
                        return self._parse_and_aggregate_records(records, target_date)
                    else:
                        logger.info(f"No records found in {url.split('/')[-1]} for {target_date}.")
                        break  # Try next URL or exit loop

                except requests.RequestException as e:
                    logger.error(f"Error fetching electricity prices: {e}")
                    if attempt < max_retries:
                        time.sleep(3 * attempt)
                        continue
                    raise

        return []

    def _parse_and_aggregate_records(self, records: List[Dict], target_date: str) -> List[Dict]:
        """
        Aggregates 15-minute intervals (or 1-hour records) into 24 standard hourly buckets.
        Calculates average spot price per hour in DKK/kWh.
        """
        hourly_mwh = defaultdict(list)
        hourly_eur = defaultdict(list)

        for r in records:
            # Handle both TimeDK (new DayAheadPrices) and HourDK (legacy Elspotprices)
            time_str = r.get("TimeDK") or r.get("HourDK") or ""
            try:
                dt = datetime.fromisoformat(time_str)
                hour = dt.hour
            except Exception:
                continue

            # DayAheadPriceDKK or SpotPriceDKK is in DKK per MWh
            price_mwh = r.get("DayAheadPriceDKK")
            if price_mwh is None:
                price_mwh = r.get("SpotPriceDKK", 0.0)

            price_eur = r.get("DayAheadPriceEUR")
            if price_eur is None:
                price_eur = r.get("SpotPriceEUR", 0.0)

            hourly_mwh[hour].append(float(price_mwh))
            hourly_eur[hour].append(float(price_eur))

        parsed = []
        for hour in range(24):
            if hour in hourly_mwh and hourly_mwh[hour]:
                avg_mwh = sum(hourly_mwh[hour]) / len(hourly_mwh[hour])
                avg_eur = sum(hourly_eur[hour]) / len(hourly_eur[hour])
                price_kwh = round(avg_mwh / 1000.0, 4)

                time_str = f"{hour:02d}:00 - {(hour + 1) % 24:02d}:00"
                if hour == 23:
                    time_str = "23:00 - 00:00"

                parsed.append({
                    "date": target_date,
                    "hour": hour,
                    "time_str": time_str,
                    "price_kwh": price_kwh,
                    "raw_mwh": round(avg_mwh, 2),
                    "price_eur_mwh": round(avg_eur, 2),
                    "quarter_count": len(hourly_mwh[hour]),
                })

        parsed.sort(key=lambda x: x["hour"])
        return parsed
