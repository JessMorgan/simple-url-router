import bcrypt
from itsdangerous import URLSafeTimedSerializer

from app.config import settings

_serializer = URLSafeTimedSerializer(secret_key=settings.secret_key, salt="admin-session")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_session_token() -> str:
    return _serializer.dumps({"user": settings.admin_username})


def verify_session_token(token: str) -> bool:
    try:
        data = _serializer.loads(token, max_age=settings.session_max_age)
        return data.get("user") == settings.admin_username
    except Exception:
        return False
