from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Query, Request

from schemas import ForecastDay, ForecastResponse, WeatherResponse
from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.client = httpx.AsyncClient(timeout=10.0)
    yield
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _extract_error(exc: Exception) -> HTTPException:
    if isinstance(exc, httpx.TimeoutException):
        return HTTPException(status_code=504, detail="upstream timeout")
    if isinstance(exc, httpx.HTTPError):
        return HTTPException(status_code=502, detail="upstream unavailable")
    return HTTPException(status_code=502, detail="unexpected upstream response")


@app.get("/weather", response_model=WeatherResponse)
async def weather(
    request: Request,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
) -> WeatherResponse:
    client: httpx.AsyncClient = request.app.state.client
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m",
    }
    try:
        response = await client.get(
            f"{settings.open_meteo_base_url}/forecast", params=params
        )
        response.raise_for_status()
        data = response.json()
        current = data["current"]
        return WeatherResponse(
            latitude=latitude,
            longitude=longitude,
            temperature=float(current["temperature_2m"]),
            wind_speed=float(current["wind_speed_10m"]),
        )
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise _extract_error(exc) from exc


@app.get("/forecast", response_model=ForecastResponse)
async def forecast(
    request: Request,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    days: int = Query(3, ge=1, le=7),
) -> ForecastResponse:
    client: httpx.AsyncClient = request.app.state.client
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "forecast_days": days,
        "daily": "temperature_2m_max,temperature_2m_min,wind_speed_10m_max",
        "timezone": "auto",
    }
    try:
        response = await client.get(
            f"{settings.open_meteo_base_url}/forecast", params=params
        )
        response.raise_for_status()
        data = response.json()
        daily = data["daily"]
        forecast_days = [
            ForecastDay(
                date=daily["time"][i],
                temp_min=float(daily["temperature_2m_min"][i]),
                temp_max=float(daily["temperature_2m_max"][i]),
                wind_speed_max=(
                    float(daily["wind_speed_10m_max"][i])
                    if daily.get("wind_speed_10m_max")
                    else None
                ),
            )
            for i in range(len(daily["time"]))
        ]
        return ForecastResponse(
            latitude=latitude,
            longitude=longitude,
            days=days,
            forecast=forecast_days,
        )
    except (httpx.HTTPError, KeyError, TypeError, ValueError, IndexError) as exc:
        raise _extract_error(exc) from exc
