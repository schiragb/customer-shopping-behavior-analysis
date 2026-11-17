"""Load the cleaned CSV into PostgreSQL (table: customer).

Credentials are read from environment variables / a local .env file
(see .env.example). Never hard-code passwords in source code.
"""
import io
import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from pandas.api.types import is_bool_dtype, is_float_dtype, is_integer_dtype
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
CLEANED = ROOT / "data" / "processed" / "customer_shopping_behavior_cleaned.csv"
TABLE = "customer"

load_dotenv(ROOT / ".env")


def sql_type(dtype) -> str:
    if is_bool_dtype(dtype):
        return "BOOLEAN"
    if is_integer_dtype(dtype):
        return "BIGINT"
    if is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    return "TEXT"


def main() -> None:
    df = pd.read_csv(CLEANED)
    conn = psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        database=os.getenv("PGDATABASE", "customer_behavior"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.environ["PGPASSWORD"],
    )
    try:
        with conn, conn.cursor() as cur:
            cols = sql.SQL(", ").join(
                sql.SQL("{} {}").format(sql.Identifier(c), sql.SQL(sql_type(df[c].dtype)))
                for c in df.columns
            )
            cur.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(TABLE)))
            cur.execute(sql.SQL("CREATE TABLE {} ({})").format(sql.Identifier(TABLE), cols))

            buf = io.StringIO()
            df.to_csv(buf, index=False, header=False, na_rep=r"\N")
            buf.seek(0)
            cur.copy_expert(
                sql.SQL("COPY {} FROM STDIN WITH (FORMAT CSV, NULL '\\N')")
                .format(sql.Identifier(TABLE))
                .as_string(conn),
                buf,
            )
            cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(TABLE)))
            print(f"Loaded {cur.fetchone()[0]} rows into '{TABLE}'")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
