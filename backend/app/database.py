import os
from urllib.parse import urlparse
import boto3
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

DEFAULT_RDS_HOST = "database-1.cluster-c7oceugkgaxi.eu-north-1.rds.amazonaws.com"
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")
raw_db_url = os.getenv("DATABASE_URL")

if CLOUD_SQL_CONNECTION_NAME:
    # Google Cloud Run: the Cloud SQL connector exposes a Unix socket under
    # /cloudsql/<project>:<region>:<instance>. The password comes from Secret
    # Manager as DB_PASSWORD; it is never part of a URL in the environment.
    raw_db_url = URL.create(
        "postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        query={"host": f"/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"},
    )
elif not raw_db_url:
    if os.getenv("AWS_EXECUTION_ENV") or os.getenv("ECS_CONTAINER_METADATA_URI") or os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI"):
        raw_db_url = f"postgresql://postgres@{DEFAULT_RDS_HOST}:5432/postgres"
    else:
        raw_db_url = "postgresql://spry:spry_pass@postgres:5432/spry_db"

DATABASE_URL = raw_db_url

if CLOUD_SQL_CONNECTION_NAME:
    # db-f1-micro allows 25 connections; at most 3 instances x 4 = 12.
    engine = create_engine(DATABASE_URL, pool_size=2, max_overflow=2, pool_pre_ping=True)
elif "rds.amazonaws.com" in DATABASE_URL:
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
