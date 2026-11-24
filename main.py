"""Weather proxy service — FastAPI application."""

from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    open_meteo_base_url: str = "https://api.open-meteo.com/v1"

    model_config = {"env_file": ".env"}


settings = Settings()


class WeatherParams(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ForecastParams(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    days: int = Field(default=3, ge=1, le=7)


class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    temperature: float
    wind_speed: float
    source: str = "open-meteo"


class ForecastDay(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    wind_speed_max: float


class ForecastResponse(BaseModel):
    latitude: float
    longitude: float
    days: int
    forecast: list[ForecastDay]
    source: str = "open-meteo"


class HealthResponse(BaseModel):
    status: str = "ok"


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        app.state.client = client
        yield


app = FastAPI(lifespan=lifespan)


async def get_client() -> httpx.AsyncClient:
    return app.state.client


async def get_weather_params(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
) -> WeatherParams:
    return WeatherParams(latitude=latitude, longitude=longitude)


async def get_forecast_params(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(default=3, ge=1, le=7),
) -> ForecastParams:
    return ForecastParams(latitude=latitude, longitude=longitude, days=days)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/weather", response_model=WeatherResponse)
async def weather(
    params: Annotated[WeatherParams, Depends(get_weather_params)],
    client: Annotated[httpx.AsyncClient, Depends(get_client)],
) -> WeatherResponse:
    url = f"{settings.open_meteo_base_url}/forecast"
    try:
        resp = await client.get(
            url,
            params={
                "latitude": params.latitude,
                "longitude": params.longitude,
                "current": "temperature_2m,wind_speed_10m",
            },
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502, detail="Unexpected response from weather service"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Weather service unavailable")

    try:
        current = data["current"]
        return WeatherResponse(
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            temperature=float(current["temperature_2m"]),
            wind_speed=float(current["wind_speed_10m"]),
        )
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=502, detail="Unexpected response from weather service"
        )


@app.get("/forecast", response_model=ForecastResponse)
async def forecast(
    params: Annotated[ForecastParams, Depends(get_forecast_params)],
    client: Annotated[httpx.AsyncClient, Depends(get_client)],
) -> ForecastResponse:
    url = f"{settings.open_meteo_base_url}/forecast"
    try:
        resp = await client.get(
            url,
            params={
                "latitude": params.latitude,
                "longitude": params.longitude,
                "forecast_days": params.days,
                "daily": "temperature_2m_max,temperature_2m_min,wind_speed_10m_max",
            },
        )
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502, detail="Unexpected response from weather service"
        )
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Weather service unavailable")

    try:
        daily = data["daily"]
        forecast_list: list[ForecastDay] = []
        for i in range(len(daily["time"])):
            forecast_list.append(
                ForecastDay(
                    date=daily["time"][i],
                    temperature_max=float(daily["temperature_2m_max"][i]),
                    temperature_min=float(daily["temperature_2m_min"][i]),
                    wind_speed_max=float(daily["wind_speed_10m_max"][i]),
                )
            )
        return ForecastResponse(
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            days=params.days,
            forecast=forecast_list,
        )
    except (KeyError, TypeError, ValueError, IndexError):
        raise HTTPException(
            status_code=502, detail="Unexpected response from weather service"
        )
