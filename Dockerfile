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

# Устанавливаем Google Chrome (новый способ без apt-key)
RUN echo "==> Installing Google Chrome..." && \
    wget -q -O /tmp/google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get update && \
    apt-get install -y /tmp/google-chrome-stable_current_amd64.deb && \
    rm /tmp/google-chrome-stable_current_amd64.deb && \
    rm -rf /var/lib/apt/lists/* && \
    google-chrome --version && \
    echo "==> Google Chrome installed successfully"

# Устанавливаем ChromeDriver (автоматически подбирает версию под Chrome)
RUN echo "==> Installing ChromeDriver..." && \
    CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1) && \
    echo "Chrome major version: $CHROME_VERSION" && \
    CHROMEDRIVER_VERSION=$(curl -sS "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_${CHROME_VERSION}") && \
    echo "ChromeDriver version: $CHROMEDRIVER_VERSION" && \
    wget -q -O /tmp/chromedriver-linux64.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver-linux64.zip -d /tmp/ && \
    mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ && \
    rm -rf /tmp/chromedriver-linux64.zip /tmp/chromedriver-linux64 && \
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
ENV CHECK_INTERVAL=180

# Проверяем что всё готово
RUN echo "==> Build completed successfully!" && \
    echo "Python version:" && python --version && \
    echo "Chrome version:" && google-chrome --version && \
    echo "ChromeDriver version:" && chromedriver --version && \
    echo "Installed packages:" && pip list | grep -E "(requests|selenium|dotenv)"

# Запускаем бота
CMD echo "==> Starting bot..." && python main.py

