# CRM-система — Django + DRF + Celery + Docker

Полнофункциональная CRM для торгово-сервисного предприятия.

---

## Стек технологий

| Слой | Технология |
|------|-----------|
| Backend | Django 5, Django REST Framework |
| Аутентификация | JWT (SimpleJWT) |
| Фоновые задачи | Celery + Redis |
| База данных | PostgreSQL (prod) / SQLite (dev) |
| Фронтенд | Bootstrap 5, Chart.js, Vanilla JS |
| Контейнеризация | Docker + Docker Compose |
| API-документация | drf-spectacular / Swagger UI |

---

## Быстрый старт (разработка)

```bash
# 1. Клонируем и устанавливаем зависимости
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Настройки (dev использует SQLite — ничего менять не нужно)
export DJANGO_SETTINGS_MODULE=crm_project.settings.development

# 3. Миграции и суперпользователь
python manage.py migrate
python manage.py createsuperuser

# 4. Запуск сервера
python manage.py runserver

# 5. (Опционально) Celery — в отдельном терминале
celery -A crm_project worker -l info
```

Открываем: http://127.0.0.1:8000

---

## Запуск через Docker Compose (продакшн)

```bash
# Копируем и заполняем переменные окружения
cp .env.example .env
# Редактируем .env: SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS, EMAIL_*

docker-compose up -d --build

# Первоначальная настройка (один раз)
docker-compose exec web python manage.py createsuperuser
```

---

## Переменные окружения (.env)

```env
SECRET_KEY=your-very-secret-key-change-me
DB_PASSWORD=supersecret
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
REDIS_URL=redis://redis:6379/0

# E-mail (опционально)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=crm@company.com
EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL=crm@company.com
```

---

## Структура проекта

```
crm_project/
├── apps/
│   ├── accounts/        # CustomUser, роли, профиль
│   ├── clients/         # Клиенты, контакты, комментарии, документы
│   ├── requests_app/    # Заявки, сигналы Celery
│   ├── deals/           # Сделки, воронка продаж
│   ├── tasks/           # Задачи, Celery-задачи (уведомления)
│   ├── reports/         # Дашборд, аналитика
│   └── api/             # DRF ViewSets, сериализаторы, роутер
├── crm_project/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── celery.py
├── templates/
│   ├── base.html        # Bootstrap 5 sidebar layout
│   ├── dashboard/
│   ├── clients/
│   ├── requests_app/    # список + Kanban
│   ├── deals/
│   ├── reports/
│   └── accounts/        # login, profile
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## API-документация

После запуска открой: **http://localhost:8000/api/docs/**

### Основные эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /api/token/ | Получить JWT-токены |
| POST | /api/token/refresh/ | Обновить access-токен |
| GET/POST | /api/clients/ | Список / создание клиентов |
| GET | /api/clients/{id}/timeline/ | Лента событий клиента |
| GET | /api/requests/kanban/ | Данные для Kanban-доски |
| PATCH | /api/requests/{id}/status/ | Смена статуса (drag-and-drop) |
| GET | /api/deals/funnel/ | Воронка продаж (Chart.js) |
| GET | /api/reports/sales/ | Отчёт по продажам |

---

## Роли пользователей

| Роль | Возможности |
|------|-------------|
| `manager` | Видит своих клиентов / заявки / сделки |
| `supervisor` | Видит всё, кроме управления пользователями |
| `admin` | Полный доступ + Django Admin |

---

## Уведомления (Celery)

- **Дедлайн заявки** — e-mail менеджеру за 24 часа до срока
- **Ежедневная проверка** — в 08:00 по расписанию
- **Еженедельный дайджест** — руководителям каждый понедельник в 09:00
