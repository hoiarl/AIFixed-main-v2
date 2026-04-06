from src.database import Base, engine

# Import SQLAlchemy models so metadata is populated.
import src.schemas.user_schemas  # noqa: F401
import src.schemas.presentation_schemas  # noqa: F401
import src.schemas.presentation_schema  # noqa: F401
import src.schemas.message_schemas  # noqa: F401
import src.schemas.tempfile_schemas  # noqa: F401

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
