import pandas as pd
import pytest

from pipeline import DataValidationError, transform, validate

def make_df(**overrides):
    data = {
        "city": ["Johannesburg"],
        "timestamp": [pd.Timestamp("2026-10-23 12:00")],
        "temperature_c": [22.0],
        "rain_mm": [0.0],
        "wind_kmh": [10.0],
    }
    data.update(overrides)
    return pd.DataFrame(data)

def test_valid_data_passes():
    validate(make_df())

def test_impossible_temperature_fails():
    with pytest.raises(DataValidationError):
        validate(make_df(temperature_c=[99.0]))

def test_missing_value_fails():
    with pytest.raises(DataValidationError):
        validate(make_df(rain_mm=[None]))    

def test_duplicate_rows_fail():
    with pytest.raises(DataValidationError):
        validate(pd.concat([make_df(), make_df()]))  

def test_transform_builds_expected_columns():
    raw = {"hourly": {"time": ["2026-10-13T12:00"], "temperature_2m": [20.5],
                    "precipitation": [0.0], "wind_speed_10m": [5.0]}}

    df = transform(raw, "Durban")
    assert list(df.columns) == ["city", "timestamp", "temperature_c", "rain_mm", "wind_kmh"]
    assert df["city"].iloc[0] == "Durban"

              
