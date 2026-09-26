"""Analyzer for electricity price data."""

from typing import Dict, List, Tuple


class PriceAnalyzer:
    def __init__(self, threshold_kwh: float = 1.0, top_count: int = 3):
        self.threshold_kwh = threshold_kwh
        self.top_count = top_count

    def get_top_cheapest(self, prices: List[Dict]) -> List[Dict]:
        """Returns the top N cheapest hours sorted by price ascending."""
        if not prices:
            return []
        sorted_prices = sorted(prices, key=lambda x: x["price_kwh"])
        return sorted_prices[: self.top_count]

    def get_hours_below_threshold(self, prices: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Finds all hours where price is below the threshold and groups
        consecutive hours into continuous time ranges.
        """
        below = [p for p in prices if p["price_kwh"] < self.threshold_kwh]
        if not below:
            return [], []

        # Sort by hour
        below_sorted = sorted(below, key=lambda x: x["hour"])

        # Group consecutive hours
        grouped = []
        current_group = [below_sorted[0]]

        for item in below_sorted[1:]:
            prev_hour = current_group[-1]["hour"]
            if item["hour"] == prev_hour + 1:
                current_group.append(item)
            else:
                grouped.append(self._format_group(current_group))
                current_group = [item]

        if current_group:
            grouped.append(self._format_group(current_group))

        return below_sorted, grouped

    def _format_group(self, group: List[Dict]) -> Dict:
        start_hour = group[0]["hour"]
        end_hour = (group[-1]["hour"] + 1) % 24
        end_str = f"{end_hour:02d}:00"
        if group[-1]["hour"] == 23:
            end_str = "00:00"

        range_str = f"{start_hour:02d}:00 - {end_str}"
        avg_price = sum(item["price_kwh"] for item in group) / len(group)

        result = {
            "start_hour": start_hour,
            "end_hour": end_hour,
            "range_str": range_str,
            "count": len(group),
            "avg_price": round(avg_price, 2),
            "hours": group,
        }

        # Include total all-inclusive average if present
        if any("total_price_kwh" in item for item in group):
            avg_total = sum(item.get("total_price_kwh", item["price_kwh"]) for item in group) / len(group)
            result["avg_total"] = round(avg_total, 2)

        return result

    def get_day_stats(self, prices: List[Dict]) -> Dict:
        """Calculates summary statistics for the day."""
        if not prices:
            return {}

        prices_values = [p["price_kwh"] for p in prices]
        min_p = min(prices_values)
        max_p = max(prices_values)
        avg_p = sum(prices_values) / len(prices_values)
        negative_hours = [p for p in prices if p["price_kwh"] < 0.0]

        stats = {
            "min_price": round(min_p, 2),
            "max_price": round(max_p, 2),
            "avg_price": round(avg_p, 2),
            "has_negative": len(negative_hours) > 0,
            "negative_hours": negative_hours,
            "total_hours": len(prices),
        }

        # Add total price stats if all-inclusive price is calculated
        total_values = [p["total_price_kwh"] for p in prices if "total_price_kwh" in p]
        if total_values:
            stats["has_totals"] = True
            stats["min_total"] = round(min(total_values), 2)
            stats["max_total"] = round(max(total_values), 2)
            stats["avg_total"] = round(sum(total_values) / len(total_values), 2)
        else:
            stats["has_totals"] = False

        return stats
