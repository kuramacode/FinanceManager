from app.clients.nbu_client import fetch_rates
import time

class CurrencyConverter():
    def __init__(self):
        self._rates = None
        self._last_update = 0
        
    def _load_rates(self):
        if self._rates is None or time.time() - self._last_update > 3600:
            self._rates = fetch_rates()
            self._last_update = time.time()
            
    def convert(self, base_currency: str, target_currency: str, amount: float):
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
            "rate": round(rate_from / rate_to, 4)
        }