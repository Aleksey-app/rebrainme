# Weather Proxy

FastAPI-прокси для погодного API Open-Meteo.

## Стек

- Python 3.12
- UV (пакетный менеджер)
- FastAPI
- httpx (`AsyncClient`)
- ruff (formatter + linter)

## Запуск

### 1. Активировать виртуальное окружение

```bash
source .venv/bin/activate
```

### 2. Установить зависимости

```bash
uv sync
```

### 3. Запустить uvicorn

```bash
uvicorn main:app --reload
```

Сервис будет доступен по адресу `http://127.0.0.1:8000`.

## Эндпоинты

### `GET /health`
```bash
curl http://127.0.0.1:8000/health
# {"status": "ok"}
```

### `GET /weather?latitude=..&longitude=..`
```bash
curl "http://127.0.0.1:8000/weather?latitude=55.7558&longitude=37.6173"
```

### `GET /forecast?latitude=..&longitude=..&days=3`
```bash
curl "http://127.0.0.1:8000/forecast?latitude=55.7558&longitude=37.6173&days=3"
```

## Конфигурация

Переменная `OPEN_METEO_BASE_URL` задаётся в файле `.env` (пример в `.env.example`).

## Проверка кода

```bash
uv run ruff format .
uv run ruff check . --fix
uv run ruff check .
```
