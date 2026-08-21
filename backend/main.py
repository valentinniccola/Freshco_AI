from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from config import settings
from routers import auth, predict, history, analytics
from migrations.migrate_db import run_migrations

# Run automatic database migrations & sync tables
run_migrations()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Based Smart Food Freshness Detection System using OpenCV, MobileNetV2 CNN, and FastAPI",
    version="1.1.0"
)

# CORS Configuration for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Folders for Uploaded and Sample Images
app.mount("/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Register API Routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {
        "system": "Freshco AI - Smart Food Freshness Detection API",
        "status": "online",
        "version": "1.1.0",
        "features": [
            "OpenCV Computer Vision & Spoilage Preprocessing",
            "MobileNetV2 CNN Freshness Classification",
            "Multi-Tier Image Validation Pipeline",
            "Food Type Identification & Zero-Waste Recipe Suggestions",
            "Analytics Dashboard with SQL Aggregation",
            "SQLite Scan History & JWT Authentication"
        ],
        "endpoints": {
            "auth": "/api/auth",
            "predict": "/api/predict",
            "samples": "/api/predict/samples",
            "history": "/api/history",
            "analytics": "/api/analytics",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
