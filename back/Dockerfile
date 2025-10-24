FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NODE_ENV=production

WORKDIR /app

# Системные зависимости: qiskit(+aer), сборка колёс, и Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ cmake ninja-build libopenblas-dev \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

# --- Node deps (axios и прочее) ---
COPY package*.json ./
RUN if [ -f package.json ]; then npm ci --omit=dev; fi

# --- Python deps ---
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

# Исходники
COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host","0.0.0.0","--port","8000"]
