"""Weather proxy service backed by the Open-Meteo API."""

from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    open_meteo_base_url: str = "https://api.open-meteo.com/v1"


settings = Settings()

app = FastAPI(title="Weather Proxy", version="0.1.0")

UPSTREAM_TIMEOUT = httpx.Timeout(10.0)


class WeatherRequest(BaseModel):
    """Query parameters for the current weather endpoint."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ForecastRequest(WeatherRequest):
    """Query parameters for the forecast endpoint."""

    days: int = Field(ge=1, le=7)


class CurrentWeatherData(BaseModel):
    temperature_2m: float
    wind_speed_10m: float


class OpenMeteoWeatherResponse(BaseModel):
    current: CurrentWeatherData


class DailyForecastData(BaseModel):
    time: list[str]
    temperature_2m_max: list[float]
    temperature_2m_min: list[float]
    wind_speed_10m_max: list[float]


class OpenMeteoForecastResponse(BaseModel):
    daily: DailyForecastData


async def fetch_json(url: str, params: dict) -> object:
    """GET the upstream URL and return the parsed JSON body.

    Raises 503 when the upstream is unavailable and 502 when it responds
    with an unexpected status or body.
    """
    try:
        async with httpx.AsyncClient(timeout=UPSTREAM_TIMEOUT) as client:
            response = await client.get(url, params=params)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503, detail="Upstream service unavailable"
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=502, detail="Unexpected response from upstream service"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502, detail="Unexpected response from upstream service"
        ) from exc


def parse_current_weather(payload: object) -> CurrentWeatherData:
    try:
        return OpenMeteoWeatherResponse.model_validate(payload).current
    except ValidationError as exc:
        raise HTTPException(
            status_code=502, detail="Unexpected response from upstream service"
        ) from exc


def parse_daily_forecast(payload: object) -> DailyForecastData:
    try:
        daily = OpenMeteoForecastResponse.model_validate(payload).daily
    except ValidationError as exc:
        raise HTTPException(
            status_code=502, detail="Unexpected response from upstream service"
        ) from exc

    lengths = {
        len(daily.time),
        len(daily.temperature_2m_max),
        len(daily.temperature_2m_min),
        len(daily.wind_speed_10m_max),
    }
    if len(lengths) != 1:
        raise HTTPException(
            status_code=502, detail="Unexpected response from upstream service"
        )
    return daily


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/weather")
async def weather(params: Annotated[WeatherRequest, Query()]) -> dict:
    payload = await fetch_json(
        f"{settings.open_meteo_base_url}/forecast",
        {
            "latitude": params.latitude,
            "longitude": params.longitude,
            "current": "temperature_2m,wind_speed_10m",
        },
    )
    current = parse_current_weather(payload)
    return {
        "latitude": params.latitude,
        "longitude": params.longitude,
        "temperature": current.temperature_2m,
        "wind_speed": current.wind_speed_10m,
        "source": "open-meteo",
    }


@app.get("/forecast")
async def forecast(params: Annotated[ForecastRequest, Query()]) -> dict:
    payload = await fetch_json(
        f"{settings.open_meteo_base_url}/forecast",
        {
            "latitude": params.latitude,
            "longitude": params.longitude,
            "daily": "temperature_2m_max,temperature_2m_min,wind_speed_10m_max",
            "forecast_days": params.days,
        },
    )
    daily = parse_daily_forecast(payload)
    forecast_entries = [
        {
            "date": day,
            "temperature_max": temp_max,
            "temperature_min": temp_min,
            "wind_speed_max": wind_max,
        }
        for day, temp_max, temp_min, wind_max in zip(
            daily.time,
            daily.temperature_2m_max,
            daily.temperature_2m_min,
            daily.wind_speed_10m_max,
        )
    ]
    return {
        "latitude": params.latitude,
        "longitude": params.longitude,
        "days": len(forecast_entries),
        "forecast": forecast_entries,
        "source": "open-meteo",
    }
