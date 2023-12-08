# python-web-hw14

## Домашнє завдання #14

У цьому домашньому завданні ми продовжуємо доопрацьовувати наш REST API застосунок із домашнього завдання 13.

### Завдання

За допомогою Sphinx створіть документацію для вашого домашнього завдання. Для цього додайте в основних модулях до необхідних функцій і методів класів рядки docstrings.
Покрийте модульними тестами модулі репозиторію домашнього завдання, використовуючи фреймворк Unittest. За основу візьміть приклад із конспекту для модуля tests/test_unit_repository_notes.py
Покрийте функціональними тестами будь-який маршрут на вибір з вашого домашнього завдання, використовуючи фреймворк pytest.

### Додаткове завдання

Покрийте ваше домашнє завдання тестами більш ніж на 95%. Для контролю використовуйте пакет pytest-cov

## Реалізація

Для запуску необхідно виконати наступні дії:

1. docker-compose --env-file app/.env up -d

2. перейти до app

3. alembic init migrations

4. Add to env:

```
from src.conf.config import settings
from src.database.models import Base
...
target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.sqlalchemy_database_url_sync)
```

5. alembic revision --autogenerate -m "Init"

6. alembic upgrade head

7. python main.py

В папці app проекту необхідно створити та налаштувати файл .env у такому форматі:

```
API_NAME=PhotoShare API
API_PROTOCOL=http
API_HOST=127.0.0.1
API_PORT=8000

SECRET_KEY_LENGTH=64
ALGORITHM=HS512

DATABASE=postgresql
DRIVER_SYNC=psycopg2
DRIVER_ASYNC=asyncpg
POSTGRES_DB=...
POSTGRES_USER=${POSTGRES_DB}
POSTGRES_PASSWORD=...
POSTGRES_HOST=${API_HOST}
POSTGRES_PORT=5432
SQLALCHEMY_DATABASE_URL_SYNC=${DATABASE}+${DRIVER_SYNC}://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
SQLALCHEMY_DATABASE_URL_ASYNC=${DATABASE}+${DRIVER_ASYNC}://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

REDIS_PROTOCOL=redis
REDIS_HOST=${API_HOST}
REDIS_PORT=6379
REDIS_USER=...
REDIS_PASSWORD=...
REDIS_URL=${REDIS_PROTOCOL}://${REDIS_USER}:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}
REDIS_EXPIRE=3600

RATE_LIMITER_TIMES=2
RATE_LIMITER_SECONDS=5

MAIL_SERVER=...
MAIL_PORT=465
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_FROM=test@test.com
MAIL_FROM_NAME=${API_NAME}

CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

TEST=False
```

Щоб записати таблицю в БД, можно обійтись без алембіка, запустивши tests/create_all.py

Щоб заповнити базу фейковими контактами, змініть тимчасово у .env параметр RATE_LIMITER_TIMES на значення, що відповідає NUMBER_OF_CONTACTS у tests/seed.py, щоб пом’якшити обмеження Ratelimiter, зареєструйтесь через Swagger або Postman, скопіюйте email та passowrd користувача у tests/seed.py, та запустіть.

Для запуску тестів за допомогою pytest (наприклад, pytest tests/test_routes_auth.py -v aбо pytest --cov) потрібно у app/.env встановити параметр TEST у True (для unit тестів не обов’язково) і збільшити RATE_LIMITER_TIMES.
