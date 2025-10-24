# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все скрипты
COPY npy_to_txt.py .
COPY quant_cpu.py .
COPY all_to_csv.py .

# Копируем директорию с данными
COPY new_G_set.npy .
COPY new_routes.npy .

# Создаем директорию для вывода
RUN mkdir -p output

# Запускаем скрипты последовательно
CMD ["python", "-c", "exec(open('npy_to_txt.py').read()); exec(open('quant_cpu.py').read()); exec(open('all_to_csv.py').read())"]
