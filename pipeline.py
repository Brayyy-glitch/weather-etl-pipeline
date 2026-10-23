import logging
import sqlite3
import time
from pathlib import Path

import pandas as pd 
import requests

logger = logging.getLogger(__name__)

API_URL = "https://api.open-meteo.com/v1/forecast"
DB_PATH = Path("data/weather.db")

MAX_ATTEMPTS = 3
WAIT_SECONDS = 2

CITIES = {
    "Johannesburg": (-26.20227, 28.04363),
    "Cape Town": (-33.92584, 18.42322),
    "Durban": (-29.8579, 31.0292)
}

def extract(city, lat, lon):
    """Fetch hourly weather for one city and return the raw JSON."""
    params = {
    "latitude": lat, 
    "longitude": lon,
    "hourly": "temperature_2m,precipitation,wind_speed_10m",
    "timezone": "Africa/Johannesburg",
    "past_days": 2,
    "forecast_days": 1
}

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            logger.info("Extracted data for %s", city)
            return response.json()    
        except requests.RequestException as exc:
            logger.warning("Attempt %d/%d failed for %s: %s",
                            attempt, MAX_ATTEMPTS, city, exc)
            if attempt == MAX_ATTEMPTS:
                logger.error("Giving up on %s", city)
                raise
            time.sleep(WAIT_SECONDS)

def transform(raw, city):
    """Turn the raw responses into a DataFrame."""
    hourly = raw["hourly"]
    df = pd.DataFrame({
        "city": city,
        "timestamp": pd.to_datetime(hourly["time"]),
        "temperature_c": hourly["temperature_2m"],
        "rain_mm": hourly["precipitation"],
        "wind_kmh": hourly["wind_speed_10m"], 
    })
    return df            

class DataValidationError(Exception):
    """Raised when the data fails a quality check."""

def validate(df):
    """Check data quality. Raises DataValidationError if anything is wrong."""

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raw = extract("Johannesburg", -26.20227, 28.04363)
    df = transform(raw, "Johannesburg") 
    print(df.head())
    print(df.dtypes)
    print(len(df))