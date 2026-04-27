# Настройка Redis (Upstash) для Vercel

## 1. Создайте Redis базу на Upstash

1. Зайдите на [upstash.com](https://upstash.com) → Sign up / Log in
2. Создайте новый Redis database:
   - Click **"Create Database"**
   - Choose **Redis**
   - Region: `eu-west-1` (или ближайшая к вам)
   - Type: `Free` (бесплатный тариф)
   - Click **Create**

3. После создания вы увидите:
   - **REST URL** (например, `https://...upstash.io`)
   - **REDIS_URL** (формат: `rediss://default:password@...upstash.io:6379`)
   - **Access Token** (токен для аутентификации)

## 2. Добавьте переменные окружения в Vercel

Для проекта **backend** на Vercel Dashboard → Settings → Environment Variables добавьте:

| Key | Value | Environment |
|-----|-------|-------------|
| `REDIS_URL` | `rediss://default:xxx@...upstash.io:6379` | Production |

*Или используйте две переменные (альтернативно):*
| `UPSTASH_REDIS_REST_URL` | `https://...upstash.io` | Production |
| `UPSTASH_REDIS_REST_TOKEN` | `your-token` | Production |

## 3. Установите redis-py

`requirements.txt` уже содержит `redis==5.0.1` — Vercel установит автоматически.

## 4. Локальный запуск с Redis (опционально)

Если хотите локально использовать Redis (например, Docker):

```bash
docker run -p 6379:6379 redis:alpine
```

Затем в `backend/.env`:
```
REDIS_URL=redis://localhost:6379
```

Без `REDIS_URL` локально используются JSON-файлы в `backend/data/`.

## 5. Деплой

```bash
cd backend
vercel --prod
```

Проверка:
```bash
curl https://your-backend.vercel.app/api/health
```

## 6. Как это работает

- **При наличии Redis (REDIS_URL задан):** все данные хранятся в Redis как JSON-строки по ключам:
  - `store:data` — филиалы
  - `holidays:data` — праздники
- **Без Redis (локально или если Redis недоступен):** fallback на JSON-файлы (`backend/data/store.json`, `holidays.json`) или on Vercel без Redis — in-memory env vars (данные теряются при рестарте).
- **Мониторинг:** Redis-данные видны в Upstash Dashboard → **Data Browser**.

## 7. Важно

- При первом запуске Redis пуст — система автоматически инициализирует структуры.
- Данные в Redis персистентны (сохраняются между cold starts).
- Стоимость: Upstash Free tier — до 10,000 запросов/день, 256MB storage.
