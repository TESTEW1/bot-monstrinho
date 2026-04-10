FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Força versão mais recente do yt-dlp com suporte a JS challenge
RUN pip install --no-cache-dir --upgrade yt-dlp mutagen brotli requests

COPY . .
CMD ["python", "bot.py"]
