import requests
from app.config import Config

class Consts:
    
    GROUPS = ['All',
              'Asia',
              'Europe',
              'Americas',
              'Other']
    
def _get_currency_json():
    response = requests.get(Config.NBU_URL)
    
    