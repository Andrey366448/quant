# back/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем запросы с любых источников
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP методы
    allow_headers=["*"],  # Разрешаем все заголовки
)

# Папка для хранения загруженных файлов
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.get("/upload/")
async def get_files():
    """
    Возвращает список всех файлов в папке.
    """
    files = os.listdir(UPLOAD_FOLDER)
    return {"files": files}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """
    Загружает файл на сервер.
    """
    with open(os.path.join(UPLOAD_FOLDER, file.filename), "wb") as f:
        f.write(await file.read())
    return {"filename": file.filename}
