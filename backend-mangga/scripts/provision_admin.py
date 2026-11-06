import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.security import hash_password
from crud.users import get_by_email
from db.session import SessionLocal
from models.domain_models import Role, User


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision a development admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    with SessionLocal() as db:
        if get_by_email(db, args.email) is not None:
            raise SystemExit("Admin email is already registered")
        db.add(
            User(
                email=args.email.lower(),
                hashed_password=hash_password(args.password),
                nama_lengkap=args.name,
                role=Role.ADMIN_GUDANG,
            )
        )
        db.commit()
    print("Admin provisioned successfully.")


if __name__ == "__main__":
    main()
