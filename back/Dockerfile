FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# системные зависимости на случай компиляции каких-то колес
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libffi-dev libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# свежие инструменты сборки + установка зависимостей
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# Открываем порт для приложения
EXPOSE 8000

# подправь путь к модулю приложения под свой проект
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

