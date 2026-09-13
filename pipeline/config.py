"""
pipeline/config.py
──────────────────
Central configuration: cities and date window.
"""

from datetime import date, timedelta

# Cities to collect weather for. Each entry is (name, latitude, longitude).
CITIES: list[dict] = [
    {"name": "London",   "latitude": 51.5074,  "longitude": -0.1278},
    {"name": "New York", "latitude": 40.7128,  "longitude": -74.0060},
    {"name": "Tokyo",    "latitude": 35.6762,  "longitude": 139.6503},
    {"name": "Sydney",   "latitude": -33.8688, "longitude": 151.2093},
    {"name": "Mumbai",   "latitude": 19.0760,  "longitude": 72.8777},
]

# Weather variables to fetch from Open-Meteo archive API
WEATHER_VARIABLES: list[str] = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "windspeed_10m_max",
]

# How many days of history to back-fill (default: last 30 days)
LOOKBACK_DAYS: int = 30


def get_date_range(lookback_days: int = LOOKBACK_DAYS) -> tuple[date, date]:
    """Return (start_date, end_date) for the fetch window.

    end_date is yesterday (Open-Meteo archive lags by ~1 day).
    """
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=lookback_days - 1)
    return start_date, end_date
