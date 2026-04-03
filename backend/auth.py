import bcrypt
from itsdangerous import URLSafeTimedSerializer
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "ejar-pro-secret-change-in-production")
SESSION_MAX_AGE = 60 * 60 * 24 * 7   # 7 days

serializer = URLSafeTimedSerializer(SECRET_KEY)
COOKIE_NAME = "ejar_session"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_session_cookie(user_id: int) -> str:
    return serializer.dumps({"uid": user_id})


def decode_session_cookie(token: str) -> dict | None:
    try:
        return serializer.loads(token, max_age=SESSION_MAX_AGE)
    except Exception:
        return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    data = decode_session_cookie(token)
    if not data:
        raise HTTPException(status_code=401, detail="Session expired")
    user = db.get(User, data["uid"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user
