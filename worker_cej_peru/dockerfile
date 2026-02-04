FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Bogota
ENV DISPLAY=:99

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    xvfb \
    xauth \
    x11-utils \
    wget \
    curl \
    gnupg \
    ca-certificates \
    apt-transport-https \
    unzip \
    sudo \
    dos2unix \
    python3-dev \
    python3-tk \
    fonts-liberation \
    libreoffice \
    libreoffice-writer \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libu2f-udev \
    libvulkan1 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxtst6 \
    libxext6 \
    libxi6 \
    libxcursor1 \
    libxfixes3 \
    libxrender1 \
    libdbus-1-3 \
    \
    # 🔽 AGREGADOS PARA LIBREOFFICE (CRÍTICOS)
    openjdk-21-jre-headless \
    libcups2 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    fonts-dejavu \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /home/app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install pydoll-python

COPY . .

CMD ["bash", "-c", "Xvfb :99 -screen 0 1920x1080x24 & python main.py"]
