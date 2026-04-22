import json
import os

import redis
from redis.exceptions import RedisError


def _build_redis_client():
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        decode_responses=True,
        socket_connect_timeout=float(os.getenv("REDIS_CONNECT_TIMEOUT", "0.2")),
        socket_timeout=float(os.getenv("REDIS_TIMEOUT", "0.2")),
    )


_redis = _build_redis_client()


class RateCache:
    KEY = "rates:latest"
    TTL = 14400

    def __init__(self, client=None):
        self._client = client or _redis

    def get_rates(self):
        try:
            data = self._client.get(self.KEY)
        except RedisError:
            return None

        if not data:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def set_rates(self, rates: dict):
        try:
            self._client.set(self.KEY, json.dumps(rates), ex=self.TTL)
            return True
        except RedisError:
            return False
