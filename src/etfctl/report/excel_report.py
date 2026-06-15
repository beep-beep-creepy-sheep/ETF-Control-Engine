from __future__ import annotations

from pathlib import Path

import pandas as pd

from etfctl.storage.duckdb_client import DuckDBClient


SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _summary(etf: pd.DataFrame, exceptions: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    row = etf.iloc[0].to_dict()
    counts = exceptions["severity"].value_counts().to_dict() if not exceptions.empty else {}
    row.update(
        {
            "total_exceptions": len(exceptions),
            "high_severity_exceptions": counts.get("HIGH", 0),
            "medium_severity_exceptions": counts.get("MEDIUM", 0),
            "low_severity_exceptions": counts.get("LOW", 0),
            "last_audit_status": audit.iloc[-1]["status"] if not audit.empty else "",
        }
    )
    return pd.DataFrame([row])


def write_excel_report(trade_date: str, db_path: str | Path, output_dir: str | Path) -> Path:
    client = DuckDBClient(db_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"ETF_Exception_Report_{trade_date}.xlsx"

    etf = client.read_df("select * from etf_valuation where trade_date = ?", [trade_date])
    basket = client.read_df("select * from basket_valuation where trade_date = ?", [trade_date])
    selected = client.read_df("select * from selected_prices where trade_date = ?", [trade_date])
    exceptions = client.read_df("select * from control_exceptions where trade_date = ?", [trade_date])
    audit = client.read_df("select * from run_audit where trade_date = ? order by created_at", [trade_date])

    if not exceptions.empty:
        exceptions["_severity_rank"] = exceptions["severity"].map(SEVERITY_ORDER).fillna(9)
        exceptions = exceptions.sort_values(["_severity_rank", "entity_id"]).drop(columns="_severity_rank")

    with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
        workbook = writer.book
        header_fmt = workbook.add_format({"bold": True, "bg_color": "#D9EAF7", "border": 1})
        for name, frame in {
            "Summary": _summary(etf, exceptions, audit),
            "ETF Valuation": etf,
            "Basket Valuation": basket,
            "Selected Prices": selected,
            "FX Checks": exceptions[exceptions["exception_type"].str.startswith("FX", na=False)] if not exceptions.empty else exceptions,
            "Drift Checks": exceptions[exceptions["exception_type"].isin(["LARGE_WEIGHT_CHANGE", "NEW_COMPONENT", "REMOVED_COMPONENT"])] if not exceptions.empty else exceptions,
            "Exceptions": exceptions,
            "Run Audit": audit,
        }.items():
            frame.to_excel(writer, sheet_name=name, index=False)
            worksheet = writer.sheets[name]
            for col_num, value in enumerate(frame.columns):
                worksheet.write(0, col_num, value, header_fmt)
                worksheet.set_column(col_num, col_num, min(max(len(str(value)) + 2, 12), 35))
    return out_path

