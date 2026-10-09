from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.core.exceptions import BadRequestException


# Static exchange rates relative to USD (base currency)
# In production, these would come from an external API or database
EXCHANGE_RATES = {
    "USD": Decimal("1.00"),
    "EUR": Decimal("0.92"),
    "GBP": Decimal("0.79"),
    "AED": Decimal("3.67"),
    "PKR": Decimal("278.50"),
    "INR": Decimal("83.25"),
    "SAR": Decimal("3.75"),
    "CAD": Decimal("1.36"),
    "AUD": Decimal("1.53"),
    "JPY": Decimal("149.50"),
}

SUPPORTED_CURRENCIES = list(EXCHANGE_RATES.keys())


class CurrencyService:
    @staticmethod
    def convert(
        amount: Decimal,
        from_currency: str,
        to_currency: str,
    ) -> Decimal:
        """Convert amount from one currency to another using static rates."""
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return amount

        if from_currency not in EXCHANGE_RATES:
            raise BadRequestException(
                f"Unsupported source currency: {from_currency}. Supported: {SUPPORTED_CURRENCIES}"
            )
        if to_currency not in EXCHANGE_RATES:
            raise BadRequestException(
                f"Unsupported target currency: {to_currency}. Supported: {SUPPORTED_CURRENCIES}"
            )

        # Convert to USD first (base), then to target
        amount_in_usd = amount / EXCHANGE_RATES[from_currency]
        amount_in_target = amount_in_usd * EXCHANGE_RATES[to_currency]

        return amount_in_target.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def get_supported_currencies() -> list:
        """Return list of supported currency codes."""
        return SUPPORTED_CURRENCIES
