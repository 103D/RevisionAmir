# Система управления ревизиями филиалов

Полноценное веб-приложение для управления периодическими ревизиями филиалов с автоматическим планированием и уведомлениями.

## 📋 Оглавление

- [Возможности](#возможности)
- [Технологии](#технологии)
- [Структура проекта](#структура-проекта)
- [Быстрый старт](#быстрый-старт)
- [Настройка базы данных](#настройка-базы-данных)
- [API Endpoints](#api-endpoints)
- [Генерация ревизий](#генерация-ревизий)
- [Тестирование](#тестирование)
- [Конфигурация уведомлений](#конфигурация-уведомлений)
- [Экспорт данных](#экспорт-данных)
- [Changelog](#changelog)

## 🆕 Changelog

### [1.1.0] - 2025-01-XX
#### Исправления
- ✅ **Thread-safety**: Добавлены блокировки `threading.RLock()` для всех операций с хранилищем
- ✅ **Валидация статусов**: Запрещена установка статуса "planned" на прошедшие даты
- ✅ **Vercel deployment**: Удалена ложная логика работы с переменными окружения, теперь всегда используется Redis
- ✅ **Performance**: Добавлен debounce (300ms) для inline-редакторов на frontend
- ✅ **Код-ревью**: Исправлены все критические и предупреждающие issues

#### Улучшения
- Упрощена архитектура `RedisStore` (удален `EnvVarStore`)
- Улучшена обработка ошибок при подключении к Redis
- Добавлена четкая документация по использованию хранилищ

### [1.0.0] - Первоначальный релиз

## 🚀 Возможности

### Основные функции
- ✅ **CRUD операции** для филиалов и праздников
- ✅ **Автоматическая генерация ревизий** каждые 3 месяца
- ✅ **Исключение выходных дней** (пятница, суббота, воскресенье)
- ✅ **Исключение праздничных дней**
- ✅ **Минимальный интервал** между ревизиями разных филиалов (≥2 дня)
- ✅ **Отображение** прошлой и следующей ревизии относительно текущей даты
- ✅ **День недели** для каждой ревизии

### Дополнительные функции
- 📊 **Экспорт в Excel/CSV**
- 📧 **Email уведомления** о предстоящих ревизиях
- 📱 **Telegram уведомления**
- 📈 **Статистика** по ревизиям
- 🔍 **Фильтрация** по филиалу и дате

## 🛠 Технологии

### Backend
- **Python 3.11+** + FastAPI
- **Redis** (основное хранилище) + JSON file fallback (для разработки)
- **Pydantic** (валидация данных)
- **openpyxl** (экспорт в Excel)

### Frontend
- **React 18** + Vite
- **@tanstack/react-query** (стейт-менеджмент)
- **Axios** (HTTP клиент)
- **react-hot-toast** (уведомления)

### Тестирование
- **pytest** (рекомендуется добавить)

## 📁 Структура проекта

```
Revision/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py           # Конфигурация
│   │   ├── main.py             # FastAPI приложение
│   │   ├── service.py          # Бизнес-логика (RevisionService)
│   │   ├── store.py            # JSON file storage (только для разработки)
│   │   ├── redis_store.py      # Redis storage (production)
│   │   ├── redis_holidays_store.py  # Redis storage для праздников
│   │   ├── schemas.py          # Pydantic модели
│   │   ├── export.py           # Экспорт в Excel
│   │   ├── holidays.py         # API для праздников
│   │   └── runtime_check.py    # Утилиты для проверки окружения
│   ├── data/
│   │   ├── store.json          # Локальное хранилище (dev)
│   │   └── holidays.json.example
│   ├── migrations/
│   │   └── 001_init.sql
│   ├── requirements.txt
│   └── REDIS_SETUP.md          # Инструкция по настройке Redis
│
├── frontend/
│   ├── src/
│   │   ├── components/         # React компоненты
│   │   │   ├── FilialsPage.jsx
│   │   │   ├── FilialCard.jsx
│   │   │   ├── CreateFilialForm.jsx
│   │   │   └── RevisionDatesSlider.jsx
│   │   ├── services/
│   │   │   └── api.js          # API клиент
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## ⚡ Быстрый старт

### Требования
- Python 3.11+
- Node.js 18+
- Redis (опционально, для production)

### 1. Клонирование и установка

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Настройка переменных окружения

Создайте файл `.env` в папке `backend/`:

```env
# Server
APP_HOST=0.0.0.0
APP_PORT=8000

# Redis (опционально, для production)
REDIS_URL=rediss://default:your-redis-password@your-redis-host:6379

# Data directory
DATA_DIR=./data
STORE_FILE=store.json
```

### 3. Запуск

```bash
# Backend (в одной консоли)
cd backend
python -m uvicorn app.main:app --reload

# Frontend (в другой консоли)
cd frontend
npm run dev
```

Откройте http://localhost:5173 в браузере.

## 🗄 Настройка хранилища

### Выбор хранилища

**Для разработки:**
- По умолчанию используется локальный JSON файл (`backend/data/store.json`)
- Не требует дополнительных настроек

**Для production (рекомендуется):**
- Используйте Redis (Upstash, AWS ElastiCache и т.д.)
- Данные сохраняются между вызовами serverless функций

### Заполнение тестовыми данными

Скопируйте пример данных:

```bash
cd backend
cp data/holidays.json.example data/holidays.json
```

Файл `store.json` создается автоматически при первом запуске.

### Миграция на Redis

1. Установите Redis:
   ```bash
   pip install redis
   ```

2. Добавьте `REDIS_URL` в `.env`

3. При запуске данные автоматически мигрируются из JSON в Redis

Подробнее: [REDIS_SETUP.md](backend/REDIS_SETUP.md)

## 📡 API Endpoints

### Филиалы

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/filials` | Список всех филиалов |
| GET | `/api/v1/filials/{id}` | Получить филиал по ID |
| POST | `/api/v1/filials` | Создать филиал |
| PUT | `/api/v1/filials/{id}` | Обновить филиал |
| PUT | `/api/v1/filials/{id}/next-revision` | Обновить следующую ревизию |
| DELETE | `/api/v1/filials/{id}` | Удалить филиал |

### Праздники

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/holidays` | Список всех праздников |
| POST | `/api/v1/holidays` | Создать праздник |
| PUT | `/api/v1/holidays/{id}` | Обновить праздник |
| DELETE | `/api/v1/holidays/{id}` | Удалить праздник |

### Экспорт

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/export/filials` | Экспорт филиалов в Excel |
| GET | `/api/v1/export/holidays` | Экспорт праздников в Excel |

### Здоровье

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/health` | Проверка работоспособности |

## 🔄 Генерация ревизий

### Алгоритм

1. **Интервал**: Каждые 3 месяца от даты первой ревизии
2. **Исключения**:
   - Пятница, суббота, воскресенье
   - Праздничные дни
3. **Минимальное расстояние**: ≥2 дня между ревизиями разных филиалов
4. **Горизонт генерации**: 24 месяца вперед

### Константы

```python
# backend/app/service.py
EXCLUDED_WEEKDAYS = {4, 5, 6}  # Пятница, суббота, воскресенье (Python: 0=Monday)
GENERATION_HORIZON_MONTHS = 24  # Генерация на 2 года вперед
ALLOWED_STATUSES = {"planned", "postponed"}
```

### Автоматическое смещение дат

Если выбранная дата попадает на выходной или праздник, система автоматически сдвигает её на ближайший рабочий день с учетом минимального расстояния от других ревизий.

## 🧪 Тестирование

```bash
# Backend (требуется установка pytest)
cd backend
pip install pytest
python -m pytest

# Frontend (сборка)
cd frontend
npm run build
```

### Планируется

- Юнит-тесты для `RevisionService`
- Интеграционные тесты для API
- E2E тесты для frontend

## 📧 Уведомления

> ⚠️ **Примечание**: Система уведомлений (Email/Telegram) запланирована для следующей версии.

## 📊 Экспорт данных

### Примеры использования API

```bash
# Excel - филиалы
curl -X GET "http://localhost:8000/api/v1/export/filials" \
  -o filials.xlsx

# Excel - праздники
curl -X GET "http://localhost:8000/api/v1/export/holidays" \
  -o holidays.xlsx

# Проверка здоровья
curl -X GET "http://localhost:8000/health"
```

### Создание филиала через API

```bash
curl -X POST "http://localhost:8000/api/v1/filials" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Филиал Астана-Север",
    "first_revision_date": "2024-02-01",
    "shortage": 0
  }'
```

### Обновление следующей ревизии

```bash
curl -X PUT "http://localhost:8000/api/v1/filials/{filial_id}/next-revision" \
  -H "Content-Type: application/json" \
  -d '{
    "next_revision_date": "2024-06-15",
    "status": "planned"
  }'
```

## 📝 Примеры данных

### Структура филиала

```json
{
  "id": "uuid",
  "name": "Филиал Астана",
  "first_revision_date": "2024-01-15",
  "previous_revision_date": "2024-04-15",
  "next_revision_date": "2024-07-15",
  "next_revision_status": "planned",
  "shortage": 0,
  "revision_dates": [
    "2024-01-15",
    "2024-04-15",
    "2024-07-15",
    "2024-10-15"
  ],
  "revision_statuses": {
    "2024-01-15": "done",
    "2024-04-15": "done",
    "2024-07-15": "planned"
  },
  "revision_shortages": {
    "2024-01-15": 0,
    "2024-04-15": 15000
  },
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-06-01T14:30:00Z"
}
```

## 🔧 Масштабирование

При масштабировании до 100+ филиалов:

1. **Thread-safety**: Все операции с хранилищем защищены `threading.RLock()`
2. **Кеширование**: React Query автоматически кеширует запросы
3. **Redis**: Обязательно для production deployment
4. **База данных**: При росте до 1000+ филиалов рекомендуется миграция на PostgreSQL

### Производительность

- Debounce 300ms на inline-редакторах снижает количество перерисовок
- Lazy loading компонентов через `Suspense`
- Оптимистичные обновления через React Query

## 📄 Лицензия

MIT License
