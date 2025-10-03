# Используем официальный Python образ
FROM python:3.11-slim

# Включаем логирование
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Устанавливаем зависимости для Chrome
RUN echo "==> Installing system dependencies..." && \
    apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/* \
    && echo "==> System dependencies installed successfully"

# Устанавливаем Google Chrome
RUN echo "==> Installing Google Chrome..." && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/* && \
    google-chrome --version && \
    echo "==> Google Chrome installed successfully"

# Устанавливаем ChromeDriver
RUN echo "==> Installing ChromeDriver..." && \
    CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    echo "ChromeDriver version: $CHROMEDRIVER_VERSION" && \
    wget -q --continue -P /tmp "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver_linux64.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver_linux64.zip && \
    chmod +x /usr/local/bin/chromedriver && \
    chromedriver --version && \
    echo "==> ChromeDriver installed successfully"

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы requirements
COPY requirements_selenium.txt requirements.txt
RUN echo "==> Requirements file copied" && cat requirements.txt

# Устанавливаем Python зависимости
RUN echo "==> Installing Python dependencies..." && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    echo "==> Python dependencies installed successfully" && \
    pip list

# Копируем код бота с автоматическим обновлением токенов
COPY main_auto.py main.py
RUN echo "==> Bot files copied" && \
    ls -lh /app/ && \
    echo "==> Checking main.py..." && \
    head -20 main.py

# Устанавливаем переменные окружения
ENV HEADLESS=true
ENV PYTHONUNBUFFERED=1
ENV CHECK_INTERVAL=300

# Проверяем что всё готово
RUN echo "==> Build completed successfully!" && \
    echo "Python version:" && python --version && \
    echo "Chrome version:" && google-chrome --version && \
    echo "ChromeDriver version:" && chromedriver --version && \
    echo "Installed packages:" && pip list | grep -E "(requests|selenium|dotenv)"

# Запускаем бота
CMD echo "==> Starting bot..." && python main.py

