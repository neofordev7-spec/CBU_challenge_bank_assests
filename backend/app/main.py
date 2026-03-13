from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import engine, Base
from app.models import user, branch, department, employee, category, asset, assignment, audit_log
from app.api import auth, branches, departments, employees, categories, assets, assignments, qrcode, audit_logs, statistics, upload, ai

Base.metadata.create_all(bind=engine)

# Startup'da demo ma'lumotlarni yaratish (agar database bo'sh bo'lsa)
try:
    from app.seed import seed
    seed()
except Exception as e:
    print(f"Seed xatosi (e'tiborsiz qoldirildi): {e}")

app = FastAPI(
    title=settings.APP_NAME,
    description="Bank ofisi aktivlarini boshqarish tizimi",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.QRCODE_DIR, exist_ok=True)

app.mount("/api/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/api/qrcodes", StaticFiles(directory=settings.QRCODE_DIR), name="qrcodes")

app.include_router(auth.router)
app.include_router(branches.router)
app.include_router(departments.router)
app.include_router(employees.router)
app.include_router(categories.router)
app.include_router(assets.router)
app.include_router(assignments.router)
app.include_router(qrcode.router)
app.include_router(audit_logs.router)
app.include_router(statistics.router)
app.include_router(upload.router)
app.include_router(ai.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
