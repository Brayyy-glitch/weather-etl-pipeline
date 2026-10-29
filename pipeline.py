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
    problems = []
    measures = ["temperature_c", "rain_mm", "wind_kmh"]

    if df.empty:
        problems.append("no rows returned")
    if df[measures].isnull().any().any():
        problems.append("missing values found")
    if df.duplicated(subset=["city", "timestamp"]).any():
        problems.append("duplicate (city, timestamp) rows found")
    if not df["temperature_c"].between(-50, 60).all():
        problems.append("temperature outside -50 to 60 C")
    if (df["rain_mm"] < 0).any():
        problems.append("negative rainfall")
    if (df["wind_kmh"] < 0).any():
        problems.append("negative wind speed")  

    if problems:
        raise DataValidationError("; ".join(problems))
    logger.info("Validation passed for %s (%d rows)", df["city"].iloc[0], len(df))
    return df  

def load(df, db_path=DB_PATH):
    """Insert new rows into SQLite. Existing (city, timestamp) are skipped."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        (r.city, r.timestamp.strftime ("%Y-%m-%d" "%H:%M:%S"),
        r.temperature_c, r.rain_mm, r.wind_kmh)
        for r in df.itertuples(index=False)
    ]

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather (
                city TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                temperature_c REAL,
                rain_mm REAL,
                wind_kmh REAL,
                PRIMARY KEY (city, timestamp)
                )
        """)

        before = conn.total_changes
        conn.executemany("INSERT OR IGNORE INTO weather VALUES (?, ?, ?, ?, ?)", rows)
        conn.commit()
        inserted = conn.total_changes - before
    finally:
        conn.close()

    logger.info("Loaded %d new rows (%d already existed)", inserted, len(rows) - inserted)        
    return inserted


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    total_inserted = 0
    for city, (lat, lon) in CITIES.items():
        raw = extract(city, lat, lon)
        df = transform(raw, city)
        validate(df)
        total_inserted += load(df)
    logger.info("Pipeline finished. %d new rows inserted.", total_inserted)    

if __name__ == "__main__":
    main()    