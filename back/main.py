# back/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from pathlib import Path
import shutil
import os

import quantum_inspired

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # можно ограничить на проде
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== пути ====
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
SERVER_DIR = BASE_DIR / "server"
VIS_DIR    = BASE_DIR / "visualised_qi"

for p in (UPLOAD_DIR, SERVER_DIR, VIS_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ✅ единый mount: всё из папки back отдаём по /static/*
# это покроет и /static/visualised_qi/*.png, и /static/submission(s).csv, и /static/total_time.csv
app.mount("/static", StaticFiles(directory=str(BASE_DIR)), name="static")

# ==== upload API ====
@app.get("/upload/")
async def get_files():
    return {"files": sorted([p.name for p in UPLOAD_DIR.iterdir() if p.is_file()])}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    temp_file_path = UPLOAD_DIR / file.filename
    with open(temp_file_path, "wb") as f:
        f.write(await file.read())

    if file.filename.endswith(".zip"):
        try:
            shutil.unpack_archive(str(temp_file_path), str(UPLOAD_DIR))
            temp_file_path.unlink(missing_ok=True)
            return {"message": f"File {file.filename} successfully uploaded and unpacked."}
        except shutil.ReadError:
            raise HTTPException(status_code=400, detail="Failed to unpack archive. It may be corrupted.")
    else:
        return {"filename": file.filename}

@app.delete("/upload/clear/")
async def clear_upload_folder():
    for p in UPLOAD_DIR.iterdir():
        if p.is_file():
            p.unlink()
    return {"message": "Файлы были очищены"}

@app.get("/download/")
async def download_files():
    archive_path = BASE_DIR / "uploads.zip"
    shutil.make_archive(str(archive_path.with_suffix("")), "zip", str(UPLOAD_DIR))
    return FileResponse(str(archive_path), media_type="application/zip", filename="uploads.zip")

@app.post("/upload/fromserver")
async def upload_from_server():
    for p in SERVER_DIR.iterdir():
        if p.is_file():
            shutil.copy(str(p), str(UPLOAD_DIR / p.name))
    return {"message": "Файлы были загружены с сервера"}

# ==== запуск алгоритмов ====
@app.post("/quant_inspired/")
async def quant_inspired():
    quantum_inspired.main()
    return {"message": "Квантово-вдохновлённый алгоритм завершил работу"}

@app.post("/quant_full/")
async def quant_full():
    quantum_inspired.main()
    return {"message": "Квантовый алгоритм завершил работу"}

# ==== визуализации ====
@app.get("/visualised_qi/")
async def list_visualised_pngs():
    files = sorted([p.name for p in VIS_DIR.glob("*.png") if p.is_file()])
    return {"files": files, "urls": [f"/static/visualised_qi/{name}" for name in files]}

@app.get("/visualised_qi/{filename}")
async def get_visualised_png(filename: str):
    path = VIS_DIR / filename
    if not (path.is_file() and path.suffix.lower() == ".png"):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(path), media_type="image/png", filename=filename)

# ==== (необязательно) явные ручки под CSV, если хочешь использовать /download/... ====
@app.get("/download/submissions.csv")
async def download_submissions_csv():
    # сначала пробуем submissions.csv, потом fallback на submission.csv
    for candidate in (BASE_DIR / "submissions.csv", BASE_DIR / "submission.csv"):
        if candidate.exists():
            return FileResponse(str(candidate), media_type="text/csv", filename="submissions.csv")
    raise HTTPException(status_code=404, detail="submissions.csv not found")

@app.get("/download/total_time.csv")
async def download_total_time_csv():
    path = BASE_DIR / "total_time.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="total_time.csv not found")
    return FileResponse(str(path), media_type="text/csv", filename="total_time.csv")
