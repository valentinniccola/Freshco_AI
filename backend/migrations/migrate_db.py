import sys
import sqlite3
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config import settings

def run_migrations():
    """
    Non-destructive SQLite Database Migration:
    Adds role, is_active, and last_login to users table.
    Creates admin_logs and agent_recipe_logs tables.
    Promotes default developer account to admin if present.
    """
    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
    
    if not db_path.exists():
        print(f"[Migration] Database file will be created on startup.")
        return

    print(f"[Migration] Inspecting database schema...")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # 1. Check existing columns in 'users' table
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "phone_number" not in columns:
            print("[Migration] Adding 'phone_number' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN phone_number VARCHAR(25) NULL")

        if "role" not in columns:
            print("[Migration] Adding 'role' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL")

        if "is_active" not in columns:
            print("[Migration] Adding 'is_active' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL")

        if "last_login" not in columns:
            print("[Migration] Adding 'last_login' column to 'users' table...")
            cursor.execute("ALTER TABLE users ADD COLUMN last_login DATETIME NULL")

        # 2. Check 'password_reset_codes' table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='password_reset_codes'")
        if not cursor.fetchone():
            print("[Migration] Creating 'password_reset_codes' table...")
            cursor.execute("""
                CREATE TABLE password_reset_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(100) NOT NULL,
                    code VARCHAR(6) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used BOOLEAN DEFAULT 0 NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_password_reset_codes_email ON password_reset_codes (email)")

        # 3. Check 'admin_logs' table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_logs'")
        if not cursor.fetchone():
            print("[Migration] Creating 'admin_logs' table...")
            cursor.execute("""
                CREATE TABLE admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL REFERENCES users(id),
                    action VARCHAR(50) NOT NULL,
                    target_user_id INTEGER REFERENCES users(id),
                    details TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # 4. Check 'agent_recipe_logs' table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_recipe_logs'")
        if not cursor.fetchone():
            print("[Migration] Creating 'agent_recipe_logs' table...")
            cursor.execute("""
                CREATE TABLE agent_recipe_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    ingredients_used TEXT NOT NULL,
                    recipe_title VARCHAR(100) NOT NULL,
                    recipe_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # 5. Automatically promote primary developer account to admin if exists
        cursor.execute("UPDATE users SET role = 'admin' WHERE email = 'valentinniccola@gmail.com' OR username = 'valentin'")
        if cursor.rowcount > 0:
            print(f"[Migration] Promoted {cursor.rowcount} developer user(s) to 'admin' role.")

        conn.commit()
        print("[Migration] All database tables and columns synced successfully.")

    except Exception as e:
        conn.rollback()
        print(f"[Migration] Migration error: {e}")
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    run_migrations()
