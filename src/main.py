import argparse
import logging
import sys
import time
from datetime import datetime

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src import config
from src.analyzer import PriceAnalyzer
from src.fetcher import ElectricityFetcher
from src.formatter import MessageFormatter
from src.notifiers.email import EmailNotifier
from src.notifiers.whatsapp import WhatsAppNotifier
from src.tariffs import TariffCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("electricity-notifier")


def run(
    target_date: str = None,
    dry_run: bool = False,
    price_area: str = None,
    threshold: float = None,
    include_tariffs: bool = None,
    grid_operator: str = None,
):
    area = price_area or config.PRICE_AREA
    thresh = threshold if threshold is not None else config.CHEAP_THRESHOLD_DKK
    top_count = config.TOP_CHEAPEST_COUNT
    tariffs_enabled = config.INCLUDE_TARIFFS if include_tariffs is None else include_tariffs
    operator = grid_operator or config.GRID_OPERATOR

    logger.info("=" * 55)
    logger.info("Starting Electricity Price Alert Job")
    logger.info(
        f"Target Area: {area} | Threshold: {thresh} kr/kWh | Top: {top_count} | All-inclusive Tariffs: {tariffs_enabled} ({operator})"
    )
    logger.info("=" * 55)

    fetcher = ElectricityFetcher(price_area=area)
    analyzer = PriceAnalyzer(threshold_kwh=thresh, top_count=top_count)
    formatter = MessageFormatter(price_area=area, threshold_kwh=thresh)

    date_to_query = target_date or fetcher.get_tomorrow_date()
    prices = fetcher.fetch_prices_for_date(date_to_query)

    # If tomorrow's data is not yet published and target_date wasn't explicitly forced, fallback to today
    if not prices and not target_date:
        today_date = datetime.now().strftime("%Y-%m-%d")
        logger.warning(
            f"Prices for tomorrow ({date_to_query}) not yet available. Checking today ({today_date})..."
        )
        time.sleep(3)
        date_to_query = today_date
        prices = fetcher.fetch_prices_for_date(date_to_query)

    if not prices:
        logger.error(f"No price data found for {date_to_query}. Exiting.")
        sys.exit(1)

    logger.info(f"Retrieved {len(prices)} hourly price records for {date_to_query}.")

    # Calculate all-inclusive tariffs if enabled
    if tariffs_enabled:
        tariff_calc = TariffCalculator(grid_operator=operator)
        for p in prices:
            breakdown = tariff_calc.calculate_total_price(
                spot_price_kwh=p["price_kwh"],
                hour=p["hour"],
                date_str=p.get("date"),
            )
            p["total_price_kwh"] = breakdown["total_price_kwh"]
            p["tariff_breakdown"] = breakdown

    # Analyze prices
    top_cheapest = analyzer.get_top_cheapest(prices)
    below_list, below_ranges = analyzer.get_hours_below_threshold(prices)
    day_stats = analyzer.get_day_stats(prices)

    # Generate message
    wa_message = formatter.format_whatsapp(
        date_str=date_to_query,
        top_cheapest=top_cheapest,
        below_ranges=below_ranges,
        total_below_count=len(below_list),
        day_stats=day_stats,
        include_tariffs=tariffs_enabled,
        grid_operator=operator,
    )

    subject = f"⚡ Electricity Forecast ({area}) - {date_to_query}"

    logger.info("\n--- PREVIEW OF FORMATTED MESSAGE ---\n" + wa_message + "\n------------------------------------")

    if dry_run:
        logger.info("[DRY RUN] Message generated successfully. No alerts dispatched.")
        return

    # Dispatch alerts
    dispatched_count = 0
    notifiers_to_run = config.NOTIFIERS_ENABLED

    if "whatsapp" in notifiers_to_run:
        wa = WhatsAppNotifier(
            phone=config.CALLMEBOT_PHONE,
            api_key=config.CALLMEBOT_API_KEY,
        )
        if wa.is_configured():
            if wa.send(subject, wa_message):
                dispatched_count += 1
        else:
            logger.warning("WhatsApp notifier enabled but CALLMEBOT_PHONE or CALLMEBOT_API_KEY not configured.")

    if "email" in notifiers_to_run:
        email = EmailNotifier(
            smtp_host=config.EMAIL_SMTP_HOST,
            smtp_port=config.EMAIL_SMTP_PORT,
            smtp_user=config.EMAIL_SMTP_USER,
            smtp_password=config.EMAIL_SMTP_PASSWORD,
            to_email=config.EMAIL_TO,
        )
        if email.is_configured():
            plain_text = formatter.format_email_plain(
                date_str=date_to_query,
                top_cheapest=top_cheapest,
                below_ranges=below_ranges,
                total_below_count=len(below_list),
                day_stats=day_stats,
                include_tariffs=tariffs_enabled,
                grid_operator=operator,
            )
            if email.send(subject, plain_text):
                dispatched_count += 1

    logger.info(f"Alert job finished. Dispatched to {dispatched_count} channel(s).")


def main():
    parser = argparse.ArgumentParser(description="Electricity Price Notification Runner")
    parser.add_argument("--date", type=str, default=None, help="Target date in YYYY-MM-DD (defaults to tomorrow)")
    parser.add_argument("--zone", type=str, default=None, help="Price zone, e.g. DK2 or DK1")
    parser.add_argument("--threshold", type=float, default=None, help="Cheap threshold in kr/kWh")
    parser.add_argument("--dry-run", action="store_true", help="Print message to console without sending alerts")
    parser.add_argument("--include-tariffs", action="store_true", default=None, help="Calculate all-inclusive price")
    parser.add_argument("--operator", type=str, default=None, help="Grid operator name (default: Radius)")

    args = parser.parse_args()
    run(
        target_date=args.date,
        dry_run=args.dry_run,
        price_area=args.zone,
        threshold=args.threshold,
        include_tariffs=args.include_tariffs,
        grid_operator=args.operator,
    )


if __name__ == "__main__":
    main()
