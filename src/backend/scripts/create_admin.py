"""Tạo ADMIN từ terminal; không cung cấp public API tự đăng ký admin."""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pydantic import EmailStr, TypeAdapter

from app.core.security import hash_password
from app.infrastructure.persistence import stores
from app.infrastructure.persistence.database import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an initial admin account")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Administrator")
    args = parser.parse_args()
    email = str(TypeAdapter(EmailStr).validate_python(args.email)).strip().lower()
    password = getpass.getpass("New admin password: ")
    if not 8 <= len(password) <= 128:
        raise SystemExit("Password must contain 8–128 characters")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match")
    with SessionLocal.begin() as db:
        if stores.one(db, "get_user_for_login", email=email):
            raise SystemExit("Email already exists; no account or role was modified")
        stores.execute(
            db,
            "insert_admin",
            email=email,
            password_hash=hash_password(password),
            full_name=args.name,
            role="ADMIN",
        )
    print("Admin account created. Login using POST /api/auth/login.")


if __name__ == "__main__":
    main()
