# Multi-stage build для оптимизации размера образа
FROM python:3.13-slim AS builder

# Установка зависимостей для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание виртуального окружения
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.13-slim

# Установка только runtime зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Копирование виртуального окружения из builder
COPY --from=builder /opt/venv /opt/venv

# Установка рабочей директории
WORKDIR /app

# Создание пользователя для запуска приложения (безопасность)
RUN useradd -m -u 1000 django && chown -R django:django /app

# Копирование кода приложения
COPY --chown=django:django . .

# Создание директорий для статики и медиа
RUN mkdir -p /app/static /app/media && \
    chown -R django:django /app/static /app/media

# Переключение на непривилегированного пользователя
USER django

# Активация виртуального окружения
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Сборка статики (можно перенести в entrypoint.sh)
RUN python manage.py collectstatic --noinput || true

# Порт для gunicorn
EXPOSE 8000

# Entrypoint для миграций и запуска
COPY --chown=django:django entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]