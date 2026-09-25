import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "trustus")

# Candidates in order of preference
primary_url = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
if primary_url.startswith("postgres://"):
    primary_url = primary_url.replace("postgres://", "postgresql://", 1)
if primary_url.startswith("postgresql://"):
    primary_url = primary_url.replace("postgresql://", "postgresql+psycopg2://", 1)

fallback_pg_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/trustus_db"
sqlite_url = "sqlite:///./nireekshak.db"

engine = None
SessionLocal = None
ACTIVE_DB_TYPE = "unknown"

for candidate_url in [primary_url, fallback_pg_url, sqlite_url]:
    try:
        if candidate_url.startswith("postgresql"):
            test_engine = create_engine(
                candidate_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3}
            )
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine = test_engine
            ACTIVE_DB_TYPE = "postgresql"
            print(f"Connected to PostgreSQL database: {candidate_url.split('@')[-1]}")
            break
        elif candidate_url.startswith("sqlite"):
            engine = create_engine(
                candidate_url,
                connect_args={"check_same_thread": False}
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            ACTIVE_DB_TYPE = "sqlite"
            print("Connected to SQLite fallback database: nireekshak.db")
            break
    except Exception as e:
        print(f"Database connection attempt failed for {candidate_url}: {e}")

if engine is not None:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    print("Warning: Could not initialize database engine.")

Base = declarative_base()

def get_db():
    """Dependency that provides an active DB session to route handlers."""
    if SessionLocal is None:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all registered tables and apply non-destructive column migrations."""
    if engine is not None:
        Base.metadata.create_all(bind=engine)
        
        # Apply PostgreSQL specific column migrations to ensure existing tables have new Phase 2 fields
        if ACTIVE_DB_TYPE == "postgresql":
            migrations = [
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_title VARCHAR(500);",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS proposed_amount NUMERIC(15, 2) DEFAULT 0.0;",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS awarded_amount NUMERIC(15, 2) DEFAULT 0.0;",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS latitude FLOAT;",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS longitude FLOAT;",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS proposed_location VARCHAR(300);",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS expected_completion_date DATE;",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS beneficiary_info VARCHAR(500);",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS supporting_documents JSON DEFAULT '[]'::json;",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS created_by VARCHAR(100) DEFAULT 'MP';",
                "ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
            ]
            with engine.connect() as conn:
                for mig in migrations:
                    try:
                        conn.execute(text(mig))
                    except Exception as e:
                        print(f"Migration notice: {e}")
                conn.commit()
                
        print("Database schema verified/created successfully.")
