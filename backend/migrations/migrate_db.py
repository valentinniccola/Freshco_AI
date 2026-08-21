import sys
import sqlite3
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config import BASE_DIR, settings
from database import engine, Base
import models

def run_migrations():
    """
    Applies database schema migrations safely without data loss:
    1. Adds phone_number column to users table if missing.
    2. Creates password_reset_codes table if missing.
    """
    print("[Migration] Starting database migration check...")

    db_path = BASE_DIR / "freshco.db"
    
    # 1. Direct SQLite column check for users table
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(users);")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "phone_number" not in columns:
                print("[Migration] Adding 'phone_number' column to 'users' table...")
                cursor.execute("ALTER TABLE users ADD COLUMN phone_number VARCHAR(25);")
                conn.commit()
                print("[Migration] 'phone_number' column added successfully.")
            else:
                print("[Migration] 'phone_number' column already exists in 'users' table.")
        
        conn.close()

    # 2. Create any missing tables (e.g. password_reset_codes)
    Base.metadata.create_all(bind=engine)
    print("[Migration] All database tables synced and verified successfully.")

if __name__ == "__main__":
    run_migrations()
