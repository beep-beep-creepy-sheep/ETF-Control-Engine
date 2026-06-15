from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


DDL_PATH = Path(__file__).with_name("ddl.sql")


class DuckDBClient:
    """Small wrapper around DuckDB used by the batch control pipeline."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def init_db(self) -> None:
        with self.connect() as con:
            con.execute(DDL_PATH.read_text(encoding="utf-8"))

    def replace_table_for_date(self, table: str, trade_date_col: str, trade_date: str, frame: pd.DataFrame) -> None:
        with self.connect() as con:
            con.execute(f"delete from {table} where {trade_date_col} = ?", [trade_date])
            con.register("incoming", frame)
            con.execute(f"insert into {table} select * from incoming")

    def replace_runtime_table(self, table: str, trade_date: str, frame: pd.DataFrame) -> None:
        with self.connect() as con:
            con.execute(f"delete from {table} where trade_date = ?", [trade_date])
            if not frame.empty:
                con.register("incoming", frame)
                con.execute(f"insert into {table} select * from incoming")

    def read_df(self, sql: str, params: list[object] | None = None) -> pd.DataFrame:
        with self.connect() as con:
            return con.execute(sql, params or []).fetchdf()

    def append_df(self, table: str, frame: pd.DataFrame) -> None:
        if frame.empty:
            return
        with self.connect() as con:
            con.register("incoming", frame)
            con.execute(f"insert into {table} select * from incoming")

