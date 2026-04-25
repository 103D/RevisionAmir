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
- **Node.js** + Express
- **JSON file storage** + custom repository layer
- **JWT** (для будущей аутентификации)

### Frontend
- **React 18** + Vite
- **React Query** (стейт-менеджмент)
- **React Router** (маршрутизация)
- **Axios** (HTTP клиент)

### Тестирование
- **Jest** (юнит-тесты)
- **Supertest** (интеграционные тесты)

## 📁 Структура проекта

```
Revision/
├── backend/
│   ├── src/
│   │   ├── config/         # Конфигурация и константы
│   │   ├── models/         # JSON-backed repositories (Filial, Holiday, Revision)
│   │   ├── storage/        # File store and query helpers
│   │   ├── routes/         # API маршруты
│   │   ├── services/       # Бизнес-логика
│   │   ├── middleware/     # Промежуточное ПО
│   │   └── index.js        # Точка входа
│   ├── tests/
│   │   ├── unit/           # Юнит-тесты
│   │   └── integration/    # Интеграционные тесты
│   └── package.json
│
├── frontend/
│   ├── src/
│   │   ├── components/    # React компоненты
│   │   ├── services/      # API сервисы
│   │   ├── hooks/         # Custom hooks
│   │   └── App.jsx        # Главный компонент
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

## ⚡ Быстрый старт

### Требования
- Node.js 18+

### 1. Клонирование и установка

```bash
# Клонировать репозиторий
cd backend
npm install

cd ../frontend
npm install
```

### 2. Настройка переменных окружения

Создайте файл `.env` в папке `backend/`:

```env
# Server
PORT=3000
NODE_ENV=development

# JSON storage
REVISION_STORE_PATH=./data/store.json

# Email (опционально)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@revisions.local

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 3. Запуск

```bash
# Backend (в одной консоли)
cd backend
npm run dev

# Frontend (в другой консоли)
cd frontend
npm run dev
```

Откройте http://localhost:5173 в браузере.

## 🗄 Настройка хранилища

### Заполнение тестовыми данными

```bash
cd backend
npm run seed
```

Будет создано:
- 5 филиалов (Астана, Алматы, Шымкент, Актобе, Караганда)
- Праздники Казахстана на 2024-2026 годы
- JSON-файл с данными в `backend/data/store.json`

## 📡 API Endpoints

### Филиалы

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/filials` | Список всех филиалов |
| GET | `/api/v1/filials/:id` | Получить филиал по ID |
| POST | `/api/v1/filials` | Создать филиал |
| PUT | `/api/v1/filials/:id` | Обновить филиал |
| DELETE | `/api/v1/filials/:id` | Удалить филиал |
| GET | `/api/v1/filials/:id/revisions` | Ревизии филиала |

### Праздники

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/holidays` | Список всех праздников |
| GET | `/api/v1/holidays/:id` | Получить праздник по ID |
| POST | `/api/v1/holidays` | Создать праздник |
| PUT | `/api/v1/holidays/:id` | Обновить праздник |
| DELETE | `/api/v1/holidays/:id` | Удалить праздник |

### Ревизии

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/v1/revisions/all` | Все ревизии (основной endpoint) |
| GET | `/api/v1/revisions` | Список ревизий с фильтрами |
| GET | `/api/v1/revisions/stats` | Статистика |
| GET | `/api/v1/revisions/upcoming` | Предстоящие ревизии |
| POST | `/api/v1/revisions/regenerate` | Перегенерировать ревизии |
| GET | `/api/v1/revisions/export` | Экспорт (csv/excel) |

### Уведомления

| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/api/v1/notifications/send` | Отправить уведомления |
| GET | `/api/v1/notifications/test/email` | Тест email |
| GET | `/api/v1/notifications/test/telegram` | Тест Telegram |

## 🔄 Генерация ревизий

### Алгоритм

1. **Интервал**: Каждые 3 месяца от даты первой ревизии
2. **Исключения**:
   - Пятница, суббота, воскресенье
   - Праздничные дни
3. **Минимальное расстояние**: ≥2 дня между ревизиями разных филиалов

### Константы

```javascript
// backend/src/config/constants.js
REVISION_INTERVAL_MONTHS = 3    // Интервал в месяцах
MIN_DAYS_BETWEEN_REVISIONS = 2   // Мин. дней между филиалами
EXCLUDED_DAYS = [5, 6, 0]        // Пятница, суббота, воскресенье
```

## 🧪 Тестирование

```bash
# Все тесты
cd backend
npm test

# Только юнит-тесты
npm run test:unit

# Только интеграционные тесты
npm run test:integration
```

### Покрытие тестами

- ✅ Генерация дат (исключение выходных)
- ✅ Исключение праздников
- ✅ Минимальное расстояние между филиалами
- ✅ API endpoints
- ✅ Валидация данных

## 📧 Конфигурация уведомлений

### Email (Gmail)

1. Включите 2FA на аккаунте Google
2. Создайте пароль приложения: https://myaccount.google.com/apppasswords
3. Добавьте в `.env`:
   ```
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

### Telegram

1. Создайте бота через @BotFather
2. Получите токен бота
3. Получите chat ID через @userinfobot
4. Добавьте в `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your-bot-token
   TELEGRAM_CHAT_ID=your-chat-id
   ```

## 📊 Экспорт данных

### Примеры использования API

```bash
# Excel
curl -X GET "http://localhost:3000/api/v1/revisions/export?format=excel" \
  -H "Content-Type: application/json" \
  -o revisions.xlsx

# CSV
curl -X GET "http://localhost:3000/api/v1/revisions/export?format=csv" \
  -H "Content-Type: application/json" \
  -o revisions.csv

# По филиалу
curl -X GET "http://localhost:3000/api/v1/revisions/export?filial_id=UUID" \
  -o revisions filial.xlsx
```

## 📝 Примеры данных

### Создание филиала

```bash
curl -X POST "http://localhost:3000/api/v1/filials" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Филиал Астана-Север",
    "first_revision_date": "2024-02-01",
    "address": "г. Астана, ул. Сыганак, 20",
    "contact_email": "astana-north@example.kz"
  }'
```

### Создание праздника

```bash
curl -X POST "http://localhost:3000/api/v1/holidays" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "День города",
    "date": "2024-09-15",
    "is_recurring": true
  }'
```

## 🔧 Масштабирование

При масштабировании до 100+ филиалов:

1. **Индексы** - уже настроены в моделях
2. **Кеширование** - React Query автоматически кеширует запросы
3. **Пагинация** - поддерживается на всех list endpoints
4. **Очереди** - для уведомлений рекомендуется использовать Bull/Redis

## 📄 Лицензия

MIT License
