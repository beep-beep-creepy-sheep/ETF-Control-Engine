from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from etfctl.report.excel_report import SEVERITY_ORDER
from etfctl.storage.duckdb_client import DuckDBClient


def write_html_report(trade_date: str, db_path: str | Path, output_dir: str | Path) -> Path:
    client = DuckDBClient(db_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"ETF_Exception_Report_{trade_date}.html"

    etf = client.read_df("select * from etf_valuation where trade_date = ?", [trade_date])
    exceptions = client.read_df("select * from control_exceptions where trade_date = ?", [trade_date])
    audit = client.read_df("select * from run_audit where trade_date = ? order by created_at", [trade_date])
    if not exceptions.empty:
        exceptions["_severity_rank"] = exceptions["severity"].map(SEVERITY_ORDER).fillna(9)
        exceptions = exceptions.sort_values(["_severity_rank", "entity_id"]).drop(columns="_severity_rank")

    env = Environment(
        loader=FileSystemLoader(Path(__file__).with_name("templates")),
        autoescape=select_autoescape(),
    )
    template = env.get_template("exception_report.html.j2")
    row = etf.iloc[0].to_dict()
    counts = exceptions["severity"].value_counts().to_dict() if not exceptions.empty else {}
    html = template.render(
        trade_date=trade_date,
        etf=row,
        exception_count=len(exceptions),
        high_count=counts.get("HIGH", 0),
        medium_count=counts.get("MEDIUM", 0),
        low_count=counts.get("LOW", 0),
        exceptions=exceptions.head(25).to_dict("records"),
        audit=audit.tail(10).to_dict("records"),
    )
    out_path.write_text(html, encoding="utf-8")
    return out_path

