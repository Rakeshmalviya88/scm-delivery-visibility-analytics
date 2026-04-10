from __future__ import annotations

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


def mysql_config() -> dict[str, str | int]:
    return {
        "host": os.getenv("SCM_MYSQL_HOST", "localhost"),
        "port": int(os.getenv("SCM_MYSQL_PORT", "3306")),
        "user": os.getenv("SCM_MYSQL_USER", "root"),
        "password": os.getenv("SCM_MYSQL_PASSWORD", ""),
        "database": os.getenv("SCM_MYSQL_DATABASE", "scm_delivery_visibility"),
    }


def mysql_url(include_database: bool = True) -> str:
    config = mysql_config()
    password = quote_plus(str(config["password"]))
    base = f"mysql+pymysql://{config['user']}:{password}@{config['host']}:{config['port']}"
    return f"{base}/{config['database']}" if include_database else base


def mysql_engine(include_database: bool = True):
    return create_engine(mysql_url(include_database=include_database), pool_pre_ping=True)