import os
from urllib.parse import urlparse
import boto3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

DEFAULT_RDS_HOST = "database-1.cluster-c7oceugkgaxi.eu-north-1.rds.amazonaws.com"
raw_db_url = os.getenv("DATABASE_URL")

if not raw_db_url:
    if os.getenv("AWS_EXECUTION_ENV") or os.getenv("ECS_CONTAINER_METADATA_URI") or os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"):
        raw_db_url = f"postgresql://postgres@{DEFAULT_RDS_HOST}:5432/postgres"
    else:
        raw_db_url = "postgresql://spry:spry_pass@postgres:5432/spry_db"

DATABASE_URL = raw_db_url

if "rds.amazonaws.com" in DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    hostname = parsed.hostname
    port = parsed.port or 5432
    user = parsed.username or "postgres"
    dbname = parsed.path.lstrip("/") or "postgres"
    region = os.getenv("AWS_REGION", "eu-north-1")

    connect_url = f"postgresql+psycopg2://{user}@{hostname}:{port}/{dbname}?sslmode=require"
    engine = create_engine(connect_url, pool_pre_ping=True)

    rds_client = boto3.client("rds", region_name=region)

    @event.listens_for(engine, "do_connect")
    def provide_token(dialect, conn_rec, cargs, cparams):
        cparams["password"] = rds_client.generate_db_auth_token(
            DBHostname=hostname,
            Port=port,
            DBUsername=user,
            Region=region,
        )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
