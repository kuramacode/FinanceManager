import unittest
from datetime import date

from redis.exceptions import ConnectionError as RedisConnectionError

from app import create_app
from app.cache.rate import RateCache
from app.content.manage import currency_service
from app.models import db
from app.services.converter import CurrencyConverter
from app.services.exchange_rates import get_latest_rates, upsert_rate_records
from tests.test_support import make_test_db_uri


class BrokenRedisClient:
    def get(self, key):
        raise RedisConnectionError("redis is unavailable")

    def set(self, key, value, ex=None):
        raise RedisConnectionError("redis is unavailable")


class BrokenCache:
    def get_rates(self):
        raise RuntimeError("cache unavailable")

    def set_rates(self, rates):
        raise RuntimeError("cache unavailable")


class TestCurrencyConversion(unittest.TestCase):
    def test_rate_cache_treats_unavailable_redis_as_cache_miss(self):
        cache = RateCache(client=BrokenRedisClient())

        self.assertIsNone(cache.get_rates())
        self.assertFalse(cache.set_rates({"UAH": 1.0, "USD": 40.0}))

    def test_converter_uses_rate_loader_when_cache_is_unavailable(self):
        converter = CurrencyConverter(
            BrokenCache(),
            rate_loader=lambda: {"UAH": 1.0, "USD": 40.0, "EUR": 50.0},
        )

        result = converter.convert("usd", "uah", 2.5)

        self.assertEqual(result["from"], "USD")
        self.assertEqual(result["to"], "UAH")
        self.assertEqual(result["result"], 100.0)

    def test_latest_rates_can_be_loaded_from_project_database(self):
        app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": make_test_db_uri(),
            }
        )

        with app.app_context():
            db.drop_all()
            db.create_all()
            upsert_rate_records(
                [
                    {
                        "base_code": "UAH",
                        "target_code": "USD",
                        "rate": 40.0,
                        "date": "20.04.2026",
                        "source": "nbu",
                    },
                    {
                        "base_code": "UAH",
                        "target_code": "USD",
                        "rate": 41.0,
                        "date": "21.04.2026",
                        "source": "nbu",
                    },
                ]
            )

            rates = get_latest_rates(["USD"])

        self.assertEqual(rates["UAH"], 1.0)
        self.assertEqual(rates["USD"], 41.0)

    def test_currency_page_rates_are_seeded_when_database_is_empty(self):
        app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": make_test_db_uri(),
            }
        )
        original_fetch_latest_rates = currency_service.fetch_latest_rates

        def fake_fetch_latest_rates(currencies=None, persist=True):
            records = [
                {
                    "base_code": "UAH",
                    "target_code": "USD",
                    "rate": 40.0,
                    "date": date.today(),
                    "source": "nbu",
                },
                {
                    "base_code": "UAH",
                    "target_code": "EUR",
                    "rate": 50.0,
                    "date": date.today(),
                    "source": "nbu",
                },
            ]
            if persist:
                upsert_rate_records(records)
            return {"UAH": 1.0, "USD": 40.0, "EUR": 50.0}, date.today()

        try:
            with app.app_context():
                db.drop_all()
                db.create_all()
                currency_service.fetch_latest_rates = fake_fetch_latest_rates

                rates, actual_date = currency_service.get_rates(
                    currency_service.get_nows_date(),
                    ["USD", "EUR"],
                )
        finally:
            currency_service.fetch_latest_rates = original_fetch_latest_rates

        self.assertEqual(actual_date, date.today().strftime("%d.%m.%Y"))
        self.assertEqual({rate["target_code"] for rate in rates}, {"USD", "EUR"})


if __name__ == "__main__":
    unittest.main()
