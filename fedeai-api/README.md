# fedeai-api

Python API backend for Telegram + REST with deterministic tool routing.

## Stack
- FastAPI
- SQLAlchemy + Postgres
- Matplotlib for charts
- Telegram webhook endpoint

## Local run
1. Copy `.env.example` to `.env` and fill values.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start:
   - `uvicorn app.main:app --app-dir fedeai-api --reload`

## Heroku
- Root `Procfile` is already configured.
- Set env vars:
  - `DATABASE_URL`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_WEBHOOK_SECRET`
  - `OPENAI_API_KEY`
  - `OPENAI_VISION_MODEL`

### Heroku bootstrap commands
```bash
heroku login
heroku create fedeai-api-prod
heroku config:set TELEGRAM_BOT_TOKEN=... TELEGRAM_WEBHOOK_SECRET=... OPENAI_API_KEY=...
heroku addons:create scheduler:standard
heroku addons:create papertrail:choklad
```

Then configure a free external Postgres (Neon/Supabase) and set:
```bash
heroku config:set DATABASE_URL=postgresql://...
```

Deploy:
```bash
git push heroku main
```

## Endpoints
- `GET /health`
- `POST /api/messages`
- `POST /api/tools/log-weight`
- `POST /api/tools/log-food`
- `POST /api/tools/log-food-photo`
- `POST /api/tools/charts`
- `GET /api/goals`
- `PUT /api/goals`
- `GET /api/reminders`
- `PUT /api/reminders`
- `POST /webhook/telegram`

## User isolation
- REST endpoints require `X-Telegram-User-Id` header.
- Queries and writes are scoped to that user id.
- Telegram webhook always scopes to `message.from.id`.

## Telegram photo flow
- Send a meal photo to the bot (optional caption).
- API downloads the image from Telegram, calls OpenAI vision, estimates macros,
  and logs to `food_logs` for that Telegram user only.

