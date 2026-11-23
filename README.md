# Weather Proxy

FastAPI-сервис, проксирующий запросы к Open-Meteo и возвращающий нормализованный JSON.

## Требования

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Установка

```bash
uv sync
cp .env.example .env
Конфигурация
В .env задаётся OPEN_METEO_BASE_URL (по умолчанию https://api.open-meteo.com/v1).

Запуск
bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
Эндпоинты
GET /health → {"status":"ok"}

GET /weather?latitude=41.7151&longitude=44.8271 — текущая погода

GET /forecast?latitude=41.7151&longitude=44.8271&days=3 — прогноз на 1..7 дней

Примеры
bash
curl -s http://127.0.0.1:8000/health
curl -s 'http://127.0.0.1:8000/weather?latitude=41.7151&longitude=44.8271' | python -m json.tool
curl -s 'http://127.0.0.1:8000/forecast?latitude=41.7151&longitude=44.8271&days=3' | python -m json.tool

# пример 422 (валидация параметров)
curl -s -o /dev/null -w '%{http_code}\n' 'http://127.0.0.1:8000/weather?latitude=999&longitude=44'
Линт
bash
uv run ruff format .
uv run ruff check .
Стек
Python 3.12, uv, FastAPI, httpx (AsyncClient), pydantic-settings, ruff.
