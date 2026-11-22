# Weather Proxy

Простой FastAPI-сервис-прокси к API [Open-Meteo](https://open-meteo.com):
текущая погода и прогноз по координатам.

## Эндпоинты

- `GET /health` — статус сервиса (`{"status": "ok"}`).
- `GET /weather?latitude=41.7151&longitude=44.8271` — температура и скорость ветра.
- `GET /forecast?latitude=41.7151&longitude=44.8271&days=3` — прогноз (температура
  и скорость ветра на каждый день, 1–7 дней).

## Установка и запуск

```bash
uv venv
uv add fastapi uvicorn httpx pydantic-settings python-dotenv ruff
```

```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Базовый URL API Open-Meteo задаётся переменной окружения `OPEN_METEO_BASE_URL`
(по умолчанию `https://api.open-meteo.com/v1`), значение можно поменять в `.env`
или в окружении.
