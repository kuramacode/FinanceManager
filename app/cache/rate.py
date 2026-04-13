import json; import redis

_redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
 
class RateCache:
    KEY = 'rates:latest'
    TTL = 14400
    
    def get_rates(self):
        data = _redis.get(self.KEY)
        
        if data:
            return json.loads(data)
        
        return None
    
    def set_rates(self, rates: dict):
        _redis.set(self.KEY, json.dumps(rates), ex=self.TTL) 