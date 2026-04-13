from app.clients.nbu_client import fetch_rates

class CurrencyConverter():
    def __init__(self, cache):
        self._rates = None
        self._cache = cache
    
    def _load_rates(self):
        rates = self._cache.get_rates()
        
        if rates:
            self._rates = rates
            return

        rates = fetch_rates()
        self._cache.set_rates(rates)
        
        self._rates = rates
            
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