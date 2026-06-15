from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from etfctl.storage.duckdb_client import DuckDBClient


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.astype(object).where(pd.notna(frame), None)
    records = clean.to_dict("records")
    for record in records:
        for key, value in record.items():
            if hasattr(value, "isoformat"):
                record[key] = value.isoformat()
    return records


def _severity_counts(exceptions: pd.DataFrame) -> dict[str, int]:
    if exceptions.empty:
        return {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    counts = exceptions["severity"].value_counts().to_dict()
    return {
        "HIGH": int(counts.get("HIGH", 0)),
        "MEDIUM": int(counts.get("MEDIUM", 0)),
        "LOW": int(counts.get("LOW", 0)),
    }


def build_dashboard_payload(trade_date: str, db_path: str | Path) -> dict[str, Any]:
    """Build a browser-friendly JSON snapshot from DuckDB control outputs."""
    client = DuckDBClient(db_path)
    etf = client.read_df("select * from etf_valuation where trade_date = ?", [trade_date])
    basket = client.read_df(
        "select * from basket_valuation where trade_date = ? order by component_weight desc",
        [trade_date],
    )
    selected = client.read_df(
        "select * from selected_prices where trade_date = ? order by ticker",
        [trade_date],
    )
    exceptions = client.read_df(
        """
        select *
        from control_exceptions
        where trade_date = ?
        order by
          case severity when 'HIGH' then 1 when 'MEDIUM' then 2 when 'LOW' then 3 else 9 end,
          entity_id,
          exception_type
        """,
        [trade_date],
    )
    audit = client.read_df(
        "select * from run_audit where trade_date = ? order by created_at desc",
        [trade_date],
    )

    if etf.empty:
        raise ValueError(f"No ETF valuation rows found for {trade_date}. Run controls first.")

    exception_types = (
        exceptions["exception_type"].value_counts().rename_axis("type").reset_index(name="count")
        if not exceptions.empty
        else pd.DataFrame(columns=["type", "count"])
    )
    price_statuses = (
        selected["price_status"].value_counts().rename_axis("status").reset_index(name="count")
        if not selected.empty
        else pd.DataFrame(columns=["status", "count"])
    )

    return {
        "tradeDate": trade_date,
        "generatedAt": pd.Timestamp.utcnow().isoformat(),
        "etf": _records(etf)[0],
        "summary": {
            "totalExceptions": int(len(exceptions)),
            "severity": _severity_counts(exceptions),
            "componentCount": int(len(basket)),
            "pricedComponentCount": int(selected["selected_price"].notna().sum()) if not selected.empty else 0,
        },
        "basket": _records(basket),
        "selectedPrices": _records(selected),
        "exceptions": _records(exceptions),
        "exceptionTypes": _records(exception_types),
        "priceStatuses": _records(price_statuses),
        "audit": _records(audit),
    }


def write_dashboard_data(
    trade_date: str,
    db_path: str | Path,
    output_dir: str | Path = "web/public/data",
) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"dashboard_{trade_date}.json"
    payload = build_dashboard_payload(trade_date, db_path)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path

