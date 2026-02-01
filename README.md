# YouTube Rising Videos Finder

Учебный проект для поиска «взлетающих» видео на YouTube: собираем кандидатов, снимаем метрики, считаем RisingScore и отправляем уведомления в Telegram.

## Что делает MVP
- **Collector**: ищет свежие видео через `search.list` (раз в 60 мин).
- **Poller**: обновляет метрики через `videos.list` + `channels.list` (раз в 15 мин).
- **Scorer**: считает RisingScore по последним 6 часам снимков.
- **Notifier**: отправляет топ-10 в Telegram (раз в день).
- **Storage**: сохраняет данные в PostgreSQL, raw JSON — в S3/MinIO (если настроено).

## Быстрый старт

### 1) Получить YouTube API key
1. Создай проект в [Google Cloud Console](https://console.cloud.google.com/).
2. Включи **YouTube Data API v3**.
3. Создай API key.

### 2) Подготовить .env
Скопируй пример:
```bash
cp .env.example .env
```
Заполни `YT_API_KEY` и Telegram-параметры (если нужно).

### 3) Запуск через Docker
```bash
docker compose up --build
```

### 4) Миграции базы
```bash
docker compose exec app alembic upgrade head
```

### 5) Добавить нишу
```bash
curl -X POST http://localhost:8000/sources \
  -H "Content-Type: application/json" \
  -d '{"name":"ai-tools","query":"ai tools tutorial","region_code":"US","relevance_language":"en"}'
```

### 6) Ручной запуск сбора и расчета
```bash
curl -X POST http://localhost:8000/run/collect?niche=ai-tools
curl -X POST http://localhost:8000/run/poll
curl "http://localhost:8000/rising?niche=ai-tools&window=6h&limit=10"
```

## Архитектура
- **FastAPI** — API и healthcheck.
- **PostgreSQL** — хранение источников, видео, каналов, снимков.
- **Redis + Celery** — фоновые задачи.
- **MinIO/S3** — raw JSON (опционально).

## RisingScore (упрощенно)
```
score = 0.45 * z(views_velocity)
      + 0.20 * z(likes_velocity)
      + 0.15 * z(comments_velocity)
      + 0.10 * z(views_per_sub)
      + 0.10 * z(engagement_rate)

score *= age_boost(age_hours)
```

## API
- `GET /health`
- `GET /sources`
- `POST /sources`
- `GET /rising?niche=...&window=6h&limit=20`
- `POST /run/collect?niche=...`
- `POST /run/poll`

## Тесты
```bash
pytest
```

## Примечания по квоте
`search.list` стоит 100 units, поэтому он запускается редко. Основная нагрузка — `videos.list` и `channels.list` пакетами.

## Telegram
Создай бота через @BotFather и укажи:
- `TG_BOT_TOKEN`
- `TG_CHAT_ID`

Сообщения идут в Markdown и автоматически дедуплицируются по `payload_hash`.
