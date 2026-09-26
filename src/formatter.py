"""Message formatters for WhatsApp and other notification channels."""

from datetime import datetime
from typing import Dict, List


class MessageFormatter:
    """
    Builds human-readable, emoji-formatted messages for WhatsApp and other channels.
    Supports displaying both raw spot prices and all-inclusive consumer prices
    (with grid tariffs, system fees, state taxes, and 25% VAT).
    """

    def __init__(self, price_area: str = "DK2", threshold_kwh: float = 1.0):
        self.price_area = price_area
        self.threshold_kwh = threshold_kwh

    def format_date_header(self, date_str: str) -> str:
        """Formats the date header, e.g., 'Sunday, 27. Sep 2026'."""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = dt.strftime("%A")
            formatted_date = dt.strftime("%d. %b %Y")
            return f"📅 *{day_name}, {formatted_date}*"
        except Exception:
            return f"📅 *{date_str}*"

    def format_whatsapp(
        self,
        date_str: str,
        top_cheapest: List[Dict],
        below_ranges: List[Dict],
        total_below_count: int,
        day_stats: Dict,
        include_tariffs: bool = False,
        grid_operator: str = "Radius",
    ) -> str:
        """Generate the complete WhatsApp message string."""
        lines = []

        # 1. Header
        lines.append(f"⚡ *Electricity Forecast ({self.price_area})* ⚡")
        lines.append(self.format_date_header(date_str))
        lines.append("")

        # 2. Top Cheapest Hours
        lines.append("📉 *Top Cheapest Hours:*")
        if top_cheapest:
            for rank, item in enumerate(top_cheapest, start=1):
                spot_val = item["price_kwh"]
                is_neg = spot_val < 0

                if include_tariffs and "total_price_kwh" in item:
                    tot_val = item["total_price_kwh"]
                    neg_tag = " 🎁" if is_neg else ""
                    price_str = f"*{spot_val:.2f} kr*{neg_tag} (Total: *{tot_val:.2f} kr*)"
                else:
                    neg_tag = " 🎁 (Negative!)" if is_neg else ""
                    price_str = f"*{spot_val:.2f} kr/kWh*{neg_tag}"

                lines.append(f"{rank}. {item['time_str']} → {price_str}")
        else:
            lines.append("• No hourly data available.")
        lines.append("")

        # 3. Hours Below Threshold (e.g. 1.00 kr)
        threshold_formatted = f"{self.threshold_kwh:.2f}".rstrip("0").rstrip(".")
        lines.append(f"🟢 *Hours Below {threshold_formatted} kr/kWh (Spot):*")

        if total_below_count == 24:
            lines.append(f"• 🎉 *All 24 hours* are below {threshold_formatted} kr!")
        elif below_ranges:
            for grp in below_ranges:
                if include_tariffs and "avg_total" in grp:
                    lines.append(
                        f"• *{grp['range_str']}* (Avg spot: {grp['avg_price']:.2f} kr → Total: *{grp['avg_total']:.2f} kr*)"
                    )
                else:
                    lines.append(f"• *{grp['range_str']}* (Avg: {grp['avg_price']:.2f} kr/kWh)")
        else:
            lines.append(f"• None (all hours are ≥ {threshold_formatted} kr/kWh)")
        lines.append("")

        # 4. Day Overview / Stats
        if day_stats:
            lines.append("📊 *Daily Overview:*")
            if include_tariffs and day_stats.get("has_totals"):
                lines.append(
                    f"• Spot Avg: {day_stats.get('avg_price', 0.0):.2f} kr (Total: *{day_stats.get('avg_total', 0.0):.2f} kr*)"
                )
                lines.append(
                    f"• Spot Range: {day_stats.get('min_price', 0.0):.2f} – {day_stats.get('max_price', 0.0):.2f} kr (Total: *{day_stats.get('min_total', 0.0):.2f} – {day_stats.get('max_total', 0.0):.2f} kr*)"
                )
            else:
                lines.append(f"• Average: {day_stats.get('avg_price', 0.0):.2f} kr/kWh")
                lines.append(
                    f"• Low / High: {day_stats.get('min_price', 0.0):.2f} – {day_stats.get('max_price', 0.0):.2f} kr/kWh"
                )

            # Warning if negative spot prices occur
            if day_stats.get("has_negative"):
                neg_times = ", ".join(h["time_str"] for h in day_stats["negative_hours"])
                lines.append(f"⚠️ *Negative spot prices during:* {neg_times}")
        lines.append("")

        # 5. Footer
        if include_tariffs:
            lines.append(f"💡 _Spot: Energi Data Service | Total: {grid_operator} + Tax + 25% Moms_")
        else:
            lines.append("💡 _Spot prices via Energi Data Service_")

        return "\n".join(lines)

    def format_email_plain(
        self,
        date_str: str,
        top_cheapest: List[Dict],
        below_ranges: List[Dict],
        total_below_count: int,
        day_stats: Dict,
        include_tariffs: bool = False,
        grid_operator: str = "Radius",
    ) -> str:
        """Plain text version suitable for email body."""
        wa_text = self.format_whatsapp(
            date_str,
            top_cheapest,
            below_ranges,
            total_below_count,
            day_stats,
            include_tariffs=include_tariffs,
            grid_operator=grid_operator,
        )
        return wa_text.replace("*", "").replace("_", "")
