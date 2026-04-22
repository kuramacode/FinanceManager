import requests


NBU_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
DEFAULT_TIMEOUT = 10


def fetch_rate_rows(timeout=DEFAULT_TIMEOUT):
    response = requests.get(NBU_URL, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_rates(timeout=DEFAULT_TIMEOUT):
    rows = fetch_rate_rows(timeout=timeout)
    rates = {}

    for item in rows:
        code = str(item.get("cc", "")).upper()
        rate = item.get("rate")
        if code and rate is not None:
            rates[code] = float(rate)

    rates["UAH"] = 1.0
    return rates
