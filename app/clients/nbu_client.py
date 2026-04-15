import requests

nbu_url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"

def fetch_rates():
    response = requests.get(nbu_url)
    response.raise_for_status()
    
    data = response.json()
    rates = {}
    
    for item in data:
        rates[item["cc"]] = item["rate"]
        
    rates["UAH"] = 1.0
    
    return rates