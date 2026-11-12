"""SQLAlchemy + SQLite con integridad referencial, archivo separado para la v2."""
import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


# Una BD nueva evita problemas al abrir bases v1 sin columnas de la v2.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartticket_v2.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 15}
    if DATABASE_URL.startswith("sqlite") else {},
)


@event.listens_for(engine, "connect")
def activar_claves_foraneas(dbapi_connection, _):
    if engine.dialect.name == "sqlite":
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    with SessionLocal() as session:
        yield session
