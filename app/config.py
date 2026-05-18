from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    base_url: str = "http://localhost:8000"
    """Base URL that redirect paths are appended to. No trailing slash."""

    admin_username: str = "admin"
    """Username for the single admin account."""

    admin_password: str = "changeme"
    """Password for the single admin account. Set via env var."""

    secret_key: str = "dev-secret-key-change-in-production"
    """Key used to sign session cookies. Must be a long random string in production."""

    db_path: str = "data/redirects.db"
    """Path to the SQLite database file, relative to the working directory."""

    session_max_age: int = 86400
    """Session cookie lifetime in seconds (default 24 hours)."""

    cookie_secure: bool = False
    """Set the Secure flag on session cookies. Enable when behind HTTPS."""

    @property
    def db_url(self) -> str:
        """SQLite connection URL for aiosqlite."""
        return f"sqlite+aiosqlite:///{self.db_path}"


settings = Settings()
