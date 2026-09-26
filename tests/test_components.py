import os
import sys
import unittest

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.analyzer import PriceAnalyzer
from src.formatter import MessageFormatter
from src.tariffs import TariffCalculator


class TestElectricityNotifier(unittest.TestCase):
    def setUp(self):
        # 24-hour realistic simulated Danish spot prices (DKK/kWh)
        self.mock_prices = [
            {"hour": 0, "time_str": "00:00 - 01:00", "price_kwh": 0.45},
            {"hour": 1, "time_str": "01:00 - 02:00", "price_kwh": 0.30},
            {"hour": 2, "time_str": "02:00 - 03:00", "price_kwh": 0.12}, # Top 1
            {"hour": 3, "time_str": "03:00 - 04:00", "price_kwh": 0.15}, # Top 2
            {"hour": 4, "time_str": "04:00 - 05:00", "price_kwh": 0.20}, # Top 3
            {"hour": 5, "time_str": "05:00 - 06:00", "price_kwh": 0.55},
            {"hour": 6, "time_str": "06:00 - 07:00", "price_kwh": 0.95},
            {"hour": 7, "time_str": "07:00 - 08:00", "price_kwh": 1.45},
            {"hour": 8, "time_str": "08:00 - 09:00", "price_kwh": 1.60},
            {"hour": 9, "time_str": "09:00 - 10:00", "price_kwh": 1.25},
            {"hour": 10, "time_str": "10:00 - 11:00", "price_kwh": 0.90},
            {"hour": 11, "time_str": "11:00 - 12:00", "price_kwh": 0.80},
            {"hour": 12, "time_str": "12:00 - 13:00", "price_kwh": 0.70},
            {"hour": 13, "time_str": "13:00 - 14:00", "price_kwh": 0.60},
            {"hour": 14, "time_str": "14:00 - 15:00", "price_kwh": 0.65},
            {"hour": 15, "time_str": "15:00 - 16:00", "price_kwh": 0.85},
            {"hour": 16, "time_str": "16:00 - 17:00", "price_kwh": 1.15},
            {"hour": 17, "time_str": "17:00 - 18:00", "price_kwh": 1.80},
            {"hour": 18, "time_str": "18:00 - 19:00", "price_kwh": 1.95},
            {"hour": 19, "time_str": "19:00 - 20:00", "price_kwh": 1.50},
            {"hour": 20, "time_str": "20:00 - 21:00", "price_kwh": 1.10},
            {"hour": 21, "time_str": "21:00 - 22:00", "price_kwh": 0.95},
            {"hour": 22, "time_str": "22:00 - 23:00", "price_kwh": 0.75},
            {"hour": 23, "time_str": "23:00 - 00:00", "price_kwh": 0.60},
        ]

    def test_top_cheapest(self):
        analyzer = PriceAnalyzer(threshold_kwh=1.0, top_count=3)
        top = analyzer.get_top_cheapest(self.mock_prices)
        self.assertEqual(len(top), 3)
        self.assertEqual(top[0]["hour"], 2)
        self.assertEqual(top[0]["price_kwh"], 0.12)
        self.assertEqual(top[1]["hour"], 3)
        self.assertEqual(top[2]["hour"], 4)

    def test_hours_below_threshold_grouping(self):
        analyzer = PriceAnalyzer(threshold_kwh=1.0, top_count=3)
        below_list, grouped = analyzer.get_hours_below_threshold(self.mock_prices)
        self.assertEqual(len(below_list), 16)
        self.assertEqual(len(grouped), 3)

        self.assertEqual(grouped[0]["range_str"], "00:00 - 07:00")
        self.assertEqual(grouped[1]["range_str"], "10:00 - 16:00")
        self.assertEqual(grouped[2]["range_str"], "21:00 - 00:00")

    def test_tariff_calculator(self):
        calc = TariffCalculator(grid_operator="Radius")
        # Night lavlast (hour 2): spot 0.12
        breakdown_night = calc.calculate_total_price(0.12, hour=2, date_str="2026-09-27")
        self.assertGreater(breakdown_night["total_price_kwh"], 0.12)
        # Peak spidslast (hour 18): spot 1.95
        breakdown_peak = calc.calculate_total_price(1.95, hour=18, date_str="2026-09-27")
        self.assertGreater(breakdown_peak["grid_tariff_kwh"], breakdown_night["grid_tariff_kwh"])

    def test_formatter_with_tariffs(self):
        calc = TariffCalculator(grid_operator="Radius")
        for p in self.mock_prices:
            res = calc.calculate_total_price(p["price_kwh"], p["hour"], "2026-09-27")
            p["total_price_kwh"] = res["total_price_kwh"]

        analyzer = PriceAnalyzer(threshold_kwh=1.0, top_count=3)
        formatter = MessageFormatter(price_area="DK2", threshold_kwh=1.0)

        top = analyzer.get_top_cheapest(self.mock_prices)
        below_list, grouped = analyzer.get_hours_below_threshold(self.mock_prices)
        stats = analyzer.get_day_stats(self.mock_prices)

        msg = formatter.format_whatsapp(
            date_str="2026-09-27",
            top_cheapest=top,
            below_ranges=grouped,
            total_below_count=len(below_list),
            day_stats=stats,
            include_tariffs=True,
            grid_operator="Radius",
        )

        self.assertIn("Total:", msg)
        self.assertIn("02:00 - 03:00 → *0.12 kr* (Total: *0.44 kr*)", msg)
        self.assertIn("Radius", msg)


if __name__ == "__main__":
    unittest.main()
