FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Força sempre a versão mais recente do yt-dlp (YouTube muda frequentemente)
RUN pip install --no-cache-dir --upgrade yt-dlp
COPY . .
# cookies.txt é copiado via COPY . . acima (coloque na pasta do projeto)
CMD ["python", "bot.py"]
