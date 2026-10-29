import pandas as pd
import pytest

from pipeline import DataValidationError, transform, validate

def make_df(**overrides):
    data = {
        "city": ["Johannesburg"],
        "timestamp": [pd.Timestamp("2026-10-23 12:00")],
        "temperature": [22.0],
        "rain_mm": [0.0],
        "wind_kmh": [10.0],
    }
    data.update(overrides)
    return pd.DataFrame(data)

def test_valid_data_passes():
    validate(make_df)

def test_impossible_temperature_fails():
    with pytest.raises(DataValidationError):
        validate(make_df(temperature_c=[99.0]))

def test_impossible_temperature_fails():
    with pytest.raises(DataValidationError):
        validate(make_df(rain_mm=[None]))                