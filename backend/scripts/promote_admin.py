import sys
import argparse
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from database import SessionLocal
from models import User, AdminLog

def promote_user(email: str = None, username: str = None, role: str = "admin"):
    db = SessionLocal()
    try:
        query = db.query(User)
        if email:
            user = query.filter(User.email == email.strip()).first()
        elif username:
            user = query.filter(User.username == username.strip()).first()
        else:
            print("[Error] Please specify either --email or --username.")
            return

        if not user:
            print(f"[Error] User not found (email: {email}, username: {username}).")
            return

        old_role = user.role
        user.role = role
        user.is_active = True
        db.commit()

        print(f"[Success] User '{user.username}' ({user.email}) updated: role changed from '{old_role}' to '{user.role}'.")

    except Exception as e:
        db.rollback()
        print(f"[Error] Failed to update user role: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Promote a user account to admin role.")
    parser.add_argument("--email", type=str, help="Email address of the user to promote.")
    parser.add_argument("--username", type=str, help="Username of the user to promote.")
    parser.add_argument("--role", type=str, default="admin", help="Role to assign (default: 'admin').")
    args = parser.parse_args()

    if not args.email and not args.username:
        # Default promote to developer account if no arguments passed
        promote_user(email="valentinniccola@gmail.com")
    else:
        promote_user(email=args.email, username=args.username, role=args.role)
