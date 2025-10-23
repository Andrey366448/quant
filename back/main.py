# back/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles
from pathlib import Path
import shutil
from zipfile import ZipFile
from uuid import uuid4
from starlette.background import BackgroundTask
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
VIS_DIR = BASE_DIR / "visualised_qi"
VIS_QI_DIR = BASE_DIR / "visualised_qi"

QF_DIR    = BASE_DIR / "quant_full"
VIS_QF_DIR= QF_DIR / "visualised_qf"

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

# ==== визуализации FULL ====
@app.get("/visualised_qf/")
async def list_visualised_qf_pngs():
    files = sorted([p.name for p in VIS_QF_DIR.glob("*.png") if p.is_file()])
    return {"files": files, "urls": [f"/static/quant_full/visualised_qf/{name}" for name in files]}

@app.get("/visualised_qf/{filename}")
async def get_visualised_qf_png(filename: str):
    path = VIS_QF_DIR / filename
    if not (path.is_file() and path.suffix.lower() == ".png"):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(path), media_type="image/png", filename=filename)


# ==== CSV download (ручки для кнопок) ====
def _csv_file_response(path: Path, download_name: str) -> FileResponse:
    if not (path.exists() and path.is_file()):
        raise HTTPException(status_code=404, detail=f"{download_name} not found")
    return FileResponse(str(path), media_type="text/csv", filename=download_name)

@app.get("/download/submission.csv")
async def download_submission_csv():
    for candidate in (BASE_DIR / "submission.csv", BASE_DIR / "submissions.csv"):
        if candidate.exists():
            return _csv_file_response(candidate, "submission.csv")
    raise HTTPException(status_code=404, detail="submission.csv not found")

@app.head("/download/submission.csv")
async def head_submission_csv():
    return await download_submission_csv()

@app.get("/download/total_time.csv")
async def download_total_time_csv():
    return _csv_file_response(BASE_DIR / "total_time.csv", "total_time.csv")

@app.head("/download/total_time.csv")
async def head_total_time_csv():
    return await download_total_time_csv()

# ==== CSV helpers/downloads ====
def _csv_file_response(path: Path, download_name: str) -> FileResponse:
    if not (path.exists() and path.is_file()):
        raise HTTPException(status_code=404, detail=f"{download_name} not found")
    return FileResponse(str(path), media_type="text/csv", filename=download_name)

# --- Вдохновлённый (root back/)
@app.get("/download/submission.csv")
async def download_submission_csv():
    for candidate in (BASE_DIR / "submission.csv", BASE_DIR / "submissions.csv"):
        if candidate.exists():
            return _csv_file_response(candidate, "submission.csv")
    raise HTTPException(status_code=404, detail="submission.csv not found")

@app.head("/download/submission.csv")
async def head_submission_csv():
    return await download_submission_csv()

@app.get("/download/total_time.csv")
async def download_total_time_csv():
    return _csv_file_response(BASE_DIR / "total_time.csv", "total_time.csv")

@app.head("/download/total_time.csv")
async def head_total_time_csv():
    return await download_total_time_csv()

# --- Полный (quant_full/)
@app.get("/download/full/submission.csv")
async def download_full_submission_csv():
    for candidate in (QF_DIR / "submission.csv", QF_DIR / "submissions.csv"):
        if candidate.exists():
            return _csv_file_response(candidate, "submission.csv")
    raise HTTPException(status_code=404, detail="submission.csv not found in quant_full")

@app.head("/download/full/submission.csv")
async def head_full_submission_csv():
    return await download_full_submission_csv()

@app.get("/download/full/total_time.csv")
async def download_full_total_time_csv():
    return _csv_file_response(QF_DIR / "total_time.csv", "total_time.csv")

@app.head("/download/full/total_time.csv")
async def head_full_total_time_csv():
    return await download_full_total_time_csv()

# --- ZIP bundle (надёжно качает "оба файла" одним кликом)
def _make_bundle(files: list[tuple[Path, str]]) -> FileResponse:
    files = [(p, n) for p, n in files if p.exists()]
    if not files:
        raise HTTPException(status_code=404, detail="No CSV files found")
    tmp_zip = BASE_DIR / f"_tmp_{uuid4().hex}.zip"
    with ZipFile(tmp_zip, "w") as zf:
        for src, arcname in files:
            zf.write(src, arcname)
    cleanup = BackgroundTask(lambda: os.remove(tmp_zip) if tmp_zip.exists() else None)
    return FileResponse(str(tmp_zip), media_type="application/zip", filename="results_csv.zip", background=cleanup)

@app.get("/download/csv/bundle/qi")
async def download_csv_bundle_qi():
    files = [
        (BASE_DIR / "submission.csv",  "submission.csv"),
        (BASE_DIR / "submissions.csv", "submission.csv"),
        (BASE_DIR / "total_time.csv",  "total_time.csv"),
    ]
    # приоритет нормального имени:
    # если есть submission.csv — исключим submissions.csv
    have_normal = (BASE_DIR / "submission.csv").exists()
    if have_normal:
        files = [f for f in files if f[0].name != "submissions.csv"]
    return _make_bundle(files)

@app.get("/download/csv/bundle/qf")
async def download_csv_bundle_qf():
    files = [
        (QF_DIR / "submission.csv",  "submission.csv"),
        (QF_DIR / "submissions.csv", "submission.csv"),
        (QF_DIR / "total_time.csv",  "total_time.csv"),
    ]
    have_normal = (QF_DIR / "submission.csv").exists()
    if have_normal:
        files = [f for f in files if f[0].name != "submissions.csv"]
    return _make_bundle(files)
