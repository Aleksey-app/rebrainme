# Project Rules (AGENTS.md)
## Tech Stack
- Language: Python 3.12
- Package manager: UV
- Web framework: FastAPI
- HTTP client for external requests: httpx (strictly use AsyncClient)
- Formatter and linter: ruff
## Mandatory Actions When Modifying Code
After ANY code change, you must run:
1. `uv run ruff format .`
2. `uv run ruff check . --fix`
Fix all linter warnings before completing the task.
## API Requirements (weather-proxy)
1. Health check: `GET /health` -> `{"status": "ok"}`
2. Current weather: `GET /weather?latitude=41.7151&longitude=44.8271`
   - Makes a request to: `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m`
   - Returns normalized JSON: `{"latitude": float, "longitude": float, "temperature": float, "wind_speed": float, "source": "open-meteo"}`
3. Forecast: `GET /forecast?latitude=41.7151&longitude=44.8271&days=3`
   - Returns the forecast for the specified number of days with the following structure:
     ```json
     {
       "latitude": float,
       "longitude": float,
       "days": int,
       "forecast": [
         {
           "date": "YYYY-MM-DD",
           "temperature_max": float,
           "temperature_min": float,
           "wind_speed_max": float
         }
       ],
       "source": "open-meteo"
     }
 ## Validation and Errors (via Pydantic)
 - latitude: from -90 to 90
 - longitude: from -180 to 180
 - days: from 1 to 7
 - Handle timeouts and unavailability of the external API (return 503 Service Unavailable).
 - Handle unexpected response format from the external API (return 502 Bad Gateway). 
 - User provided invalid parameters -> return a clear 422 Unprocessable Entity (FastAPI does this automatically via Pydantic).
 ## Configuration
 - The base URL of the external API must be stored in a `.env` file or via pydantic-settings.
 - Create a `.env.example` with the required variables.
