from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.users import UserRole
from app.models import AppUser


@dataclass(frozen=True)
class DuplicateUserError(ValueError):
    detail: str


def normalize_display_name(name: str) -> str:
    return name.strip().lower()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def assert_email_available(db: Session, email: str) -> None:
    normalized = normalize_email(email)
    existing = db.query(AppUser).filter(AppUser.email_normalized == normalized).first()
    if existing:
        raise DuplicateUserError(f"User already exists with role '{existing.role}'")


def build_app_user(*, role: UserRole, name: str, email: str) -> AppUser:
    return AppUser(
        role=role.value,
        display_name=name,
        display_name_normalized=normalize_display_name(name),
        email=email,
        email_normalized=normalize_email(email),
    )


def translate_user_integrity_error(exc: IntegrityError) -> DuplicateUserError | None:
    message = str(exc.orig).lower()
    if "app_users.display_name_normalized" in message:
        return DuplicateUserError("User already exists with that display name")
    if "app_users.email_normalized" in message:
        return DuplicateUserError("User already exists with that email")
    return None
