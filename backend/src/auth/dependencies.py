from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.schemas.user_schemas import User


GUEST_EMAIL = "guest@local.app"
GUEST_NAME = "Guest"


def ensure_guest_user(db: Session) -> User:
    user = db.query(User).filter_by(email=GUEST_EMAIL).first()
    if user:
        return user

    user = User(
        name=GUEST_NAME,
        email=GUEST_EMAIL,
        password=None,
        provider="guest",
        avatar=None,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    Приложение работает в режиме гостя без авторизации.
    Всегда возвращаем единственного гостевого пользователя.
    """
    return ensure_guest_user(db)


def get_current_user_optional(db: Session = Depends(get_db)) -> Optional[User]:
    return ensure_guest_user(db)
