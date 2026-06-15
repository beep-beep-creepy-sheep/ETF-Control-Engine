from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Type
from uuid import uuid4

import pandas as pd
from pydantic import BaseModel

from etfctl.config import prior_holdings_path, raw_path
from etfctl.ingest.file_audit import file_hash
from etfctl.ingest.schemas import CorporateActionRow, ETFQuoteRow, FXRow, HoldingsRow, PCFRow, PriceRow
from etfctl.storage.duckdb_client import DuckDBClient


LOAD_SPECS: dict[str, tuple[str, Type[BaseModel], str, str]] = {
    "pcf": ("raw_pcf", PCFRow, "trade_date", "pcf"),
    "holdings": ("raw_holdings", HoldingsRow, "trade_date", "holdings"),
    "prices": ("raw_prices", PriceRow, "trade_date", "prices"),
    "fx": ("raw_fx", FXRow, "trade_date", "fx"),
    "corporate_actions": (
        "raw_corporate_actions",
        CorporateActionRow,
        "effective_date",
        "corporate_actions",
    ),
    "etf_quotes": ("raw_etf_quotes", ETFQuoteRow, "trade_date", "etf_quotes"),
}


def _read_validated_csv(path: Path, model: Type[BaseModel]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")
    frame = pd.read_csv(path, keep_default_na=False, na_values=[""])
    records = frame.where(pd.notna(frame), None).to_dict("records")
    for record in records:
        model.model_validate(record)
    return frame


def ingest_raw_files(trade_date: str, db_path: str | Path) -> str:
    """Validate sample CSV files, load them into DuckDB, and write file audit rows."""
    client = DuckDBClient(db_path)
    client.init_db()
    run_id = f"RUN-{trade_date}-{uuid4().hex[:8]}"
    audit_rows: list[dict[str, object]] = []

    for file_type, (table, model, trade_date_col, path_stem) in LOAD_SPECS.items():
        path = raw_path(path_stem, trade_date)
        frame = _read_validated_csv(path, model)
        client.replace_table_for_date(table, trade_date_col, trade_date, frame)
        audit_rows.append(
            {
                "run_id": run_id,
                "trade_date": trade_date,
                "file_type": file_type,
                "file_path": str(path),
                "file_hash": file_hash(path),
                "row_count": len(frame),
                "status": "LOADED",
                "message": "validated and loaded",
                "created_at": datetime.now(UTC),
            }
        )

    prior_path = prior_holdings_path(trade_date)
    prior_frame = _read_validated_csv(prior_path, HoldingsRow)
    client.replace_table_for_date("raw_prior_holdings", "trade_date", str(prior_frame["trade_date"].iloc[0]), prior_frame)
    audit_rows.append(
        {
            "run_id": run_id,
            "trade_date": trade_date,
            "file_type": "prior_holdings",
            "file_path": str(prior_path),
            "file_hash": file_hash(prior_path),
            "row_count": len(prior_frame),
            "status": "LOADED",
            "message": "validated and loaded",
            "created_at": datetime.now(UTC),
        }
    )

    client.append_df("run_audit", pd.DataFrame(audit_rows))
    return run_id
