import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field


def validate_key(v: str) -> str:
    if len(v) > 256:
        raise ValueError("Key must be 256 characters or fewer")
    if not re.match(r"^[a-zA-Z0-9_\-./@+=:]+$", v):
        raise ValueError(
            "Key contains invalid characters. Allowed: letters, digits, and _-./@+=:"
        )
    if ".." in v:
        raise ValueError("Key must not contain path traversal (..)")
    return v


KeyParam = Annotated[str, AfterValidator(validate_key)]


def validate_path(v: str) -> str:
    if not isinstance(v, str):
        raise ValueError("Path must be a string")
    if len(v) > 2048:
        raise ValueError("Path must be 2048 characters or fewer")
    if re.match(r"^(https?:|ftps?:|//)", v, re.IGNORECASE):
        raise ValueError("Path must not contain a URI scheme")
    if ".." in v:
        raise ValueError("Path must not contain path traversal (..)")
    if not v.startswith("/"):
        raise ValueError("Path must start with /")
    if re.search(r"[\x00-\x1f\x7f]", v):
        raise ValueError("Path contains control characters")
    return v


PathValue = Annotated[str, AfterValidator(validate_path)]


class RedirectCreate(BaseModel):
    path: PathValue


class RedirectResponse(BaseModel):
    key: str
    path: str
    created_at: str | None = None
    updated_at: str | None = None


class KeyListResponse(BaseModel):
    redirects: list[RedirectResponse]
    total: int
