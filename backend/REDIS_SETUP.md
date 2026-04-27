# Настройка Redis (Upstash) для Vercel

## 1. Создайте Redis на Upstash

1. Зайдите на [upstash.com](https://upstash.com) → Sign up / Log in
2. Click **"Create Database"**
3. Выберите:
   - **Type**: `Redis`
   - **Region**: `eu-west-1` (или ближайшая к вашей аудитории)
   - **Plan**: `Free`
4. Click **Create Database**

---

## 2. Получите `REDIS_URL`

1. Откройте созданную базу
2. Перейдите в раздел **"Connect"**
3. Выберите вкладку **"Redis"** (не "REST")
4. Скопируйте значение `REDIS_URL`

Пример:
```
REDIS_URL=rediss://default:xxxxxxxx@abc123.upstash.io:6379
```

**ВАЖНО:** Используйте именно `rediss://` (с двойным `s`). Это SSL-соединение, которое требуется для Upstash.

---

## 3. Добавьте `REDIS_URL` в Vercel

Backend project → **Settings** → **Environment Variables** → **Add Variable**:

| Key | Value | Environment |
|-----|-------|-------------|
| `REDIS_URL` | `rediss://default:xxxxxxxx@abc123.upstash.io:6379` | Production |

Нажмите **Save**.

---

## 4. Деплой бэкенда

```bash
cd backend
vercel --prod
```

При первом запуске с `REDIS_URL` бэкенд:
- Подключится к Redis
- Автоматически мигрирует данные из локальных JSON-файлов (`backend/data/store.json`, `holidays.json`) в Redis
- Вы увидите в логах:
  ```
  ✓ Connected to Redis: rediss://default:...
  ✓ Migrated store.json to Redis (N filials)
  ✓ Migrated holidays.json to Redis (M holidays)
  ```

---

## 5. Проверка

**Логи:**
```bash
vercel logs <backend-project-name> --since 5m
```

**Upstash Dashboard:**
- Откройте базу → **Data Browser**
- Проверьте ключи:
  - `store:data` — данные филиалов (JSON)
  - `holidays:data` — праздники (JSON)

**API:**
```bash
curl https://your-backend.vercel.app/api/health
# {"status":"ok"}

curl https://your-backend.vercel.app/api/v1/filials
# [{"id":"...", "name":"...", ...}]
```

---

## 6. Локальный запуск (опционально)

Без `REDIS_URL` бэкенд использует JSON-файлы (`backend/data/`).

С Redis локально:
```bash
# Запустите Redis (Docker)
docker run -p 6379:6379 redis:alpine

# В backend/.env:
REDIS_URL=redis://localhost:6379

# Запуск
uvicorn app.main:app --reload
```

---

## 7. Ошибки и решения

### "Connection closed by server"
**Причина:** используется `http://` или `https://` вместо `rediss://`, или не хватает SSL.

**Решение:** Установите `REDIS_URL` с префиксом `rediss://`.

### "Authentication required."
**Причина:** неверный пароль (токен) в URL.

**Решение:** перекопируйте `REDIS_URL` из Upstash Dashboard (вкладка "Connect" → "Redis").

### "Name or service not known"
**Причина:** регион/хост недоступен.

**Решение:** Убедитесь, что Redis создан в регионе, доступном из Vercel (например, `eu-west-1`, `us-east-1`). Обновите базу если нужно.

---

## 8. Что происходит при деплое

1. Vercel устанавливает `redis==5.0.1` из `requirements.txt`
2. При старте функции `RedisStore.__init__()`:
   - читает `REDIS_URL` из env
   - подключается к Redis с retry (3 попытки)
   - если ключей `store:data`/`holidays:data` нет → мигрирует из локальных JSON-файлов
3. Все CRUD операции работают напрямую с Redis
4. Если Redis недоступен → fallback на JSON-файлы (локально) или env vars (Vercel, in-memory)

---

## 9. Миграция данных

**Автоматическая** — при первом запуске с Redis (если ключи пусты).

**Ручная** (если нужно перезаписать данные):
```bash
cd backend
export REDIS_URL=rediss://default:xxxx@...upstash.io:6379
python migrate_to_redis.py
```

---

## 10. Важно

- **Data persistence**: Redis сохраняет данные между redeploy. JSON-файлы на Vercel не сохраняются.
- **Free tier**: 10,000 операций/день, 256MB. Для активного использования может потребоваться paid plan.
- **SSL**: Upstash требует SSL (`rediss://`). Код отключает проверку сертификата (`ssl_cert_reqs=None`) для совместимости.
- **Region**: выбирайте регион, близкий к вашим пользователям (или к Vercel edge network).

---

После настройки `REDIS_URL` и деплоя бэкенда задеплойте фронтенд с `VITE_API_URL` pointing to backend URL.
