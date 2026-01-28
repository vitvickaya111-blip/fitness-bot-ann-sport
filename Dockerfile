# Multi-stage build для оптимизации размера образа
FROM python:3.11-slim as base

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 botuser && \
    mkdir -p /app/data && \
    chown -R botuser:botuser /app

WORKDIR /app

# Копирование установленных пакетов из base stage
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Копирование исходного кода
COPY --chown=botuser:botuser . .

# Переключение на непривилегированного пользователя
USER botuser

# Создание volume для базы данных
VOLUME ["/app/data"]

# Запуск бота
CMD ["python", "bot.py"]
