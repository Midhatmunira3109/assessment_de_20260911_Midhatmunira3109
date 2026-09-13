"""
pipeline/extract.py
───────────────────
Fetch daily weather data from the Open-Meteo archive API.
No API key required — the archive endpoint is publicly accessible.

API docs: https://open-meteo.com/en/docs/historical-weather-api
"""

import logging
from datetime import date

import requests

from pipeline.config import CITIES, WEATHER_VARIABLES, get_date_range

logger = logging.getLogger(__name__)

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_city(
    city: dict,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Fetch weather for a single city between start_date and end_date.

    Returns a list of dicts, one per day, with keys:
        city, date, temp_max, temp_min, precipitation_sum, windspeed_max
    """
    params = {
        "latitude": city["latitude"],
        "longitude": city["longitude"],
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": ",".join(WEATHER_VARIABLES),
        "timezone": "UTC",
    }

    logger.info("Fetching %s from %s to %s", city["name"], start_date, end_date)
    response = requests.get(ARCHIVE_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    daily = data["daily"]
    dates = daily["time"]
    temp_max = daily["temperature_2m_max"]
    temp_min = daily["temperature_2m_min"]
    precip = daily["precipitation_sum"]
    wind = daily["windspeed_10m_max"]

    records = []
    for i, d in enumerate(dates):
        records.append(
            {
                "city": city["name"],
                "date": d,
                "temp_max_c": temp_max[i],
                "temp_min_c": temp_min[i],
                "precipitation_mm": precip[i],
                "windspeed_max_kmh": wind[i],
                "latitude": city["latitude"],
                "longitude": city["longitude"],
            }
        )

    logger.info("  → %d records", len(records))
    return records


def extract_all(
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Extract weather for all configured cities.

    If start_date / end_date are not provided, uses the default lookback window
    from config.get_date_range().

    Returns a flat list of weather records.
    """
    if start_date is None or end_date is None:
        start_date, end_date = get_date_range()

    all_records: list[dict] = []
    for city in CITIES:
        records = fetch_city(city, start_date, end_date)
        all_records.extend(records)

    logger.info("Total records extracted: %d", len(all_records))
    return all_records


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    records = extract_all()
    print(f"Extracted {len(records)} records")
    print(records[:2])
