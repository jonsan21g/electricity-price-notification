"""Tariff and tax calculator for Danish electricity consumers."""

from datetime import datetime
from typing import Dict, Optional


class TariffCalculator:
    """
    Calculates Danish grid tariffs, Energinet transmission/system fees,
    state electricity tax (Elafgift), and 25% VAT (moms).
    Supports Radius Elnet (Greater Copenhagen / Nordsjælland) with Tarifmodel 3.0.
    """

    def __init__(self, grid_operator: str = "Radius"):
        self.grid_operator = grid_operator.capitalize()

        # Energinet national tariffs (excl. VAT)
        self.energinet_system_tariff = 0.0630  # 6.3 øre
        self.energinet_trans_tariff = 0.0530   # 5.3 øre
        self.energinet_total = self.energinet_system_tariff + self.energinet_trans_tariff

        # State electricity tax (Elafgift) in 2026/2027 (excl. VAT)
        self.state_tax = 0.0080  # 0.8 øre (EU minimum rate)

        # Danish VAT (Moms)
        self.vat_rate = 0.25  # 25%

    def is_winter(self, date_str: Optional[str] = None) -> bool:
        """Determines if the date falls in winter tariff period (Oct 1 - Mar 31)."""
        if not date_str:
            month = datetime.now().month
        else:
            try:
                month = datetime.strptime(date_str, "%Y-%m-%d").month
            except Exception:
                month = datetime.now().month
        # Winter is Oct (10), Nov (11), Dec (12), Jan (1), Feb (2), Mar (3)
        return month in (10, 11, 12, 1, 2, 3)

    def get_grid_tariff(self, hour: int, is_winter_season: bool) -> float:
        """
        Returns grid tariff (excl. VAT) in DKK/kWh for Radius Elnet (Tarifmodel 3.0).
        """
        if self.grid_operator == "Radius":
            # Lavlast: 00:00 - 06:00
            if 0 <= hour < 6:
                return 0.1061

            # Spidslast: 17:00 - 21:00
            elif 17 <= hour < 21:
                return 0.7583 if is_winter_season else 0.4141

            # Højlast: 06:00 - 17:00 & 21:00 - 24:00
            else:
                return 0.2528 if is_winter_season else 0.1593

        # Default fallback if unknown grid operator
        return 0.15

    def calculate_total_price(self, spot_price_kwh: float, hour: int, date_str: Optional[str] = None) -> Dict:
        """
        Calculates the complete breakdown and all-inclusive price per kWh.
        Formula:
          Total = (Spot + GridTariff + EnerginetTariff + Elafgift) * (1 + VAT)
        """
        winter = self.is_winter(date_str)
        grid_tariff = self.get_grid_tariff(hour, winter)
        subtotal_excl_vat = spot_price_kwh + grid_tariff + self.energinet_total + self.state_tax
        vat_amount = subtotal_excl_vat * self.vat_rate
        total_price = subtotal_excl_vat + vat_amount

        return {
            "spot_price_kwh": round(spot_price_kwh, 4),
            "grid_tariff_kwh": round(grid_tariff, 4),
            "energinet_kwh": round(self.energinet_total, 4),
            "state_tax_kwh": round(self.state_tax, 4),
            "subtotal_excl_vat": round(subtotal_excl_vat, 4),
            "vat_amount": round(vat_amount, 4),
            "total_price_kwh": round(total_price, 2),
        }
