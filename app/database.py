from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, sessionmaker

from app.config import get_database_url


class Base(AsyncAttrs, MappedAsDataclass, DeclarativeBase):
    pass


engine = None
SessionLocal = None


def configure_engine() -> None:
    """Replace the global engine and session factory when DATABASE_URL changes."""
    global engine, SessionLocal
    if engine is not None:
        engine.dispose()
    url = get_database_url()
    engine = create_engine(url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


configure_engine()
