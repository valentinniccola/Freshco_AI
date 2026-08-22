import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from config import settings
from routers import auth, predict, history, analytics, admin, agent_recipe
from migrations.migrate_db import run_migrations

# Create all database tables on startup
try:
    Base.metadata.create_all(bind=engine)
    run_migrations()
except Exception as e:
    print(f"[Startup Notice] Database initialization/migration notice: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Based Smart Food Freshness Detection System using OpenCV, MobileNetV2 CNN, and FastAPI",
    version="1.2.0"
)

# CORS Configuration for React Frontend
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

frontend_url = settings.FRONTEND_URL or os.environ.get("FRONTEND_URL", "")
if frontend_url:
    for url in frontend_url.split(","):
        clean_url = url.strip().rstrip("/")
        if clean_url and clean_url not in allowed_origins:
            allowed_origins.append(clean_url)

# Add CORS Middleware with Vercel Preview URL Regex Support
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if not (not frontend_url and os.environ.get("VERCEL")) else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app" if frontend_url else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Folders for Uploaded and Sample Images (if directory exists)
if settings.UPLOAD_DIR.exists():
    app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")

if settings.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Register API Routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(analytics.router)
app.include_router(admin.router)
app.include_router(agent_recipe.router)

@app.get("/")
def root():
    return {
        "system": "Freshco AI - Smart Food Freshness Detection API",
        "status": "online",
        "version": "1.2.0",
        "environment": "vercel-serverless" if os.environ.get("VERCEL") else "standalone",
        "features": [
            "OpenCV Computer Vision & Spoilage Preprocessing",
            "MobileNetV2 CNN Freshness Classification",
            "12-Class Food-Type Identification Engine",
            "Agentic Multi-Item Zero-Waste Recipe Synthesizer",
            "Role-Based Admin Dashboard & User Management",
            "Analytics Dashboard with SQL Aggregation",
            "Scan History & JWT Authentication"
        ],
        "endpoints": {
            "auth": "/api/auth",
            "predict": "/api/predict",
            "samples": "/api/predict/samples",
            "history": "/api/history",
            "analytics": "/api/analytics",
            "admin": "/api/admin",
            "agent_recipe": "/api/agent/recipe-suggestion",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
