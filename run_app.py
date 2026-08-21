"""
Freshco AI - Unified Launcher Script
Runs FastAPI Backend (Port 8000) and React Vite Frontend (Port 5173) concurrently.
"""

import subprocess
import sys
import time
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"

def run():
    print("=" * 65)
    print("  🌿 Freshco AI - Smart Food Freshness Detection System 🌿")
    print("=" * 65)
    print("  [Backend]  FastAPI running at: http://127.0.0.1:8000")
    print("  [Frontend] React + Vite at:    http://127.0.0.1:5173")
    print("  [API Docs] Swagger UI at:      http://127.0.0.1:8000/docs")
    print("=" * 65)
    print("Starting services (Press Ctrl+C to terminate)...\n")

    # Start FastAPI Backend
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=str(BACKEND_DIR)
    )

    time.sleep(1.5)

    # Start React Vite Frontend
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(FRONTEND_DIR)
    )

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping Freshco AI services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done. Goodbye!")

if __name__ == "__main__":
    run()
