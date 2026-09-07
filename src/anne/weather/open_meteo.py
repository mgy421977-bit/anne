"""Minimal Open-Meteo client; results are ephemeral observations by policy."""
from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen


_CODES = {
    0: "açık",
    1: "çoğunlukla açık",
    2: "parçalı bulutlu",
    3: "kapalı",
    45: "sisli",
    48: "kırağılı sis",
    51: "hafif çisenti",
    61: "hafif yağmur",
    63: "orta şiddette yağmur",
    65: "kuvvetli yağmur",
    71: "hafif kar",
    73: "orta şiddette kar",
    75: "kuvvetli kar",
    80: "sağanak",
    81: "orta şiddette sağanak",
    82: "kuvvetli sağanak",
    95: "gök gürültülü fırtına",
}


class OpenMeteoWeather:
    """Fetch current weather for a city without making it durable memory."""

    def __init__(self, timeout: float = 8.0) -> None:
        self.timeout = timeout

    def _get_json(self, url: str, params: dict) -> dict:
        query = urlencode(params)
        with urlopen(f"{url}?{query}", timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def observe(self, city: str) -> dict:
        geo = self._get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": city, "count": 1, "language": "tr", "format": "json"},
        )
        results = geo.get("results") or []
        if not results:
            raise ValueError(f"location not found: {city}")
        place = results[0]
        forecast = self._get_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,weather_code",
                "timezone": "auto",
            },
        )
        current = forecast.get("current", {})
        return {
            "location": place.get("name", city),
            "temperature_c": current.get("temperature_2m"),
            "condition": _CODES.get(current.get("weather_code"), "hava durumu kodu bilinmiyor"),
            "observed_at": current.get("time"),
            "durability": "ephemeral",
            "source": "Open-Meteo",
        }


__all__ = ["OpenMeteoWeather"]
