from app.services.exchange_rates import get_latest_rates, normalize_currency_code


class CurrencyConverter:
    def __init__(self, cache, rate_loader=None):
        self._rates = None
        self._cache = cache
        self._rate_loader = rate_loader or get_latest_rates

    def _load_rates(self):
        rates = None

        if self._cache is not None:
            try:
                rates = self._cache.get_rates()
            except Exception:
                rates = None

        if not rates:
            rates = self._rate_loader()

        if not rates:
            raise ValueError("Exchange rates are not available")

        rates = {normalize_currency_code(code): float(rate) for code, rate in rates.items()}

        if self._cache is not None:
            try:
                self._cache.set_rates(rates)
            except Exception:
                pass

        self._rates = rates

    def convert(self, base_currency: str, target_currency: str, amount: float):
        base_currency = normalize_currency_code(base_currency)
        target_currency = normalize_currency_code(target_currency)

        self._load_rates()
        if base_currency not in self._rates:
            raise ValueError(f"Unsupported currency: {base_currency}")

        if target_currency not in self._rates:
            raise ValueError(f"Unsupported currency: {target_currency}")

        rate_from = self._rates[base_currency]
        rate_to = self._rates[target_currency]

        result = amount * (rate_from / rate_to)

        return {
            "from": base_currency,
            "to": target_currency,
            "amount": amount,
            "result": round(result, 2),
            "rate": round(rate_from / rate_to, 4),
        }
