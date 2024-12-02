import os
from pathlib import Path

import psycopg
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def create_tables() -> None:
    with psycopg.connect(conninfo=os.environ["DATABASE_URI"]) as conn:
        sql_tables = (Path(__file__).parent.resolve() / "tables.sql").read_text()
        conn.execute(sql_tables)


if __name__ == "__main__":
    create_tables()
