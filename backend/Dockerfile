FROM python:3.11-slim
WORKDIR /app

# Копируем файл зависимостей и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY . .

# Открываем порт для приложения
EXPOSE 8000

# Команда запуска Uvicorn-сервера
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
