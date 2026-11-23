from pydantic import BaseModel, Field


class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    temperature: float
    wind_speed: float
    source: str = "open-meteo"


class ForecastDay(BaseModel):
    date: str
    temp_min: float
    temp_max: float
    wind_speed_max: float | None = None


class ForecastResponse(BaseModel):
    latitude: float
    longitude: float
    days: int = Field(ge=1, le=7)
    forecast: list[ForecastDay]
    source: str = "open-meteo"
