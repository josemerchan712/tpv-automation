"""
Creates the initial admin user if it does not already exist.

Usage:
    cd backend
    python -m scripts.seed_admin

Override defaults via environment variables:
    ADMIN_USERNAME=myadmin ADMIN_PASSWORD=strongpass python -m scripts.seed_admin
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.models  # noqa: F401 — registers all models with Base.metadata

from app.database import Base, SessionLocal, engine
from app.models.user import User, UserRole
from app.services.auth_service import get_password_hash, get_user_by_username

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin1234")

if ADMIN_PASSWORD == "admin1234":
    print(
        "[seed] WARNING: Using the default admin password 'admin1234'. "
        "Set ADMIN_PASSWORD env var to a secure value before deploying to production."
    )


def seed_admin() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if get_user_by_username(db, ADMIN_USERNAME):
            print(f"[seed] Admin user '{ADMIN_USERNAME}' already exists — skipping.")
            return
        db.add(
            User(
                username=ADMIN_USERNAME,
                password_hash=get_password_hash(ADMIN_PASSWORD),
                role=UserRole.admin,
            )
        )
        db.commit()
        print(f"[seed] Created admin user '{ADMIN_USERNAME}' (role=admin).")
    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()
