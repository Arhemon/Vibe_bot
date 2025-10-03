# Простой Dockerfile для API версии (без Chrome)
FROM python:3.11-slim

# Логирование
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN echo "==> Installing dependencies..." && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip list && \
    echo "==> Dependencies installed!"

# Копируем код
COPY main_simple.py main.py
RUN echo "==> Bot ready!" && ls -lh

# Переменные
ENV CHECK_INTERVAL=180

# Запуск
CMD echo "==> Starting bot..." && python main.py
