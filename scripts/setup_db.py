from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.mysql_utils import mysql_config, mysql_engine, mysql_url

SCHEMA_PATH = ROOT / "src" / "database" / "schema.sql"
RAW_DIR = ROOT / "data" / "raw"


TABLES = [
    "distribution_centers",
    "customers",
    "carriers",
    "routes",
    "shipments",
    "tracking_events",
]


def _run_sql_script(connection, schema_sql: str) -> None:
    statements = [statement.strip() for statement in schema_sql.split(";") if statement.strip()]
    for statement in statements:
        connection.execute(text(statement))


def setup_db() -> None:
    config = mysql_config()
    server_engine = mysql_engine(include_database=False)
    database_url = mysql_url(include_database=True)

    with server_engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{config['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )

    engine = mysql_engine(include_database=True)

    with engine.begin() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
        _run_sql_script(connection, schema_sql)
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    for table in TABLES:
        csv_path = RAW_DIR / f"{table}.csv"
        df = pd.read_csv(csv_path)
        df.to_sql(table, engine, if_exists="append", index=False, chunksize=500)

    print(f"Database created and seeded in MySQL at: {database_url}")


if __name__ == "__main__":
    setup_db()
