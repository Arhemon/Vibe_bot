# Dockerfile для полностью автоматической версии
FROM python:3.11-slim

# Логирование
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Устанавливаем системные зависимости
RUN echo "==> Installing system dependencies..." && \
    apt-get update && apt-get install -y \
    wget curl unzip gnupg ca-certificates \
    fonts-liberation libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libgbm1 \
    libgtk-3-0 libnss3 libxcomposite1 libxdamage1 \
    libxrandr2 xdg-utils \
    && rm -rf /var/lib/apt/lists/* \
    && echo "==> System dependencies OK"

# Устанавливаем Chrome
RUN echo "==> Installing Chrome..." && \
    wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && apt-get install -y /tmp/chrome.deb && \
    rm /tmp/chrome.deb && rm -rf /var/lib/apt/lists/* && \
    google-chrome --version && \
    echo "==> Chrome OK"

# Устанавливаем ChromeDriver
RUN echo "==> Installing ChromeDriver..." && \
    CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1) && \
    DRIVER_VERSION=$(curl -sS "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION}") && \
    wget -q -O /tmp/driver.zip "https://storage.googleapis.com/chrome-for-testing-public/${DRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/driver.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ && \
    rm -rf /tmp/driver.zip /tmp/chromedriver-linux64 && \
    chmod +x /usr/local/bin/chromedriver && \
    chromedriver --version && \
    echo "==> ChromeDriver OK"

WORKDIR /app

# Устанавливаем Python зависимости
COPY requirements_selenium.txt requirements.txt
RUN echo "==> Installing Python packages..." && \
    pip install --no-cache-dir -r requirements.txt && \
    pip list && \
    echo "==> Python packages OK"

# Копируем код
COPY main_final.py main.py
RUN echo "==> Bot code ready!"

# Переменные
ENV HEADLESS=true
ENV CHECK_INTERVAL=180

# Запуск
CMD python main.py
