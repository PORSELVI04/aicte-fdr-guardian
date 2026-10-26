from getpass import getpass

from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password


def main():
    Base.metadata.create_all(bind=engine)

    username = input("Enter admin username: ").strip()
    email = input("Enter admin email: ").strip()
    password = getpass("Enter admin password (minimum 8 characters): ")

    if len(username) < 3:
        print("Username must contain at least 3 characters.")
        return

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    db = SessionLocal()

    try:
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            print("Username or email already exists. Choose another.")
            return

        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="ADMIN",
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print(f"Admin account '{username}' created successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
