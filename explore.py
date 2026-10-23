import json
import requests

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": -26.20227, 
    "longitude": 28.04363,
    "hourly": "temperature_2m,precipitation,wind_speed_10m",
    "timezone": "Africa/Johannesburg",
    "past_days": 2,
    "forecast_days": 1
}

response = requests.get(url, params=params, timeout=10)
print(response.status_code)
print(json.dumps(response.json(), indent=2) [:1500])