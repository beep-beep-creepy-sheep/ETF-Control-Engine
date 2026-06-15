from __future__ import annotations

from pathlib import Path

import typer

from etfctl.engine import run_controls as run_controls_engine
from etfctl.ingest.loaders import ingest_raw_files
from etfctl.report.dashboard_data import write_dashboard_data
from etfctl.report.excel_report import write_excel_report
from etfctl.report.html_report import write_html_report
from etfctl.storage.duckdb_client import DuckDBClient


app = typer.Typer(help="Synthetic ETF basket control engine CLI.")


@app.command("init-db")
def init_db(db: Path = typer.Option(..., help="DuckDB database path.")) -> None:
    DuckDBClient(db).init_db()
    typer.echo(f"Initialized DuckDB database at {db}")


@app.command("ingest")
def ingest(date: str = typer.Option(..., "--date"), db: Path = typer.Option(...)) -> None:
    run_id = ingest_raw_files(date, db)
    typer.echo(f"Ingest completed for {date}. run_id={run_id}")


@app.command("run-controls")
def run_controls(date: str = typer.Option(..., "--date"), db: Path = typer.Option(...)) -> None:
    run_id = run_controls_engine(date, db)
    typer.echo(f"Controls completed for {date}. run_id={run_id}")


@app.command("report")
def report(
    date: str = typer.Option(..., "--date"),
    db: Path = typer.Option(...),
    output: Path = typer.Option(...),
) -> None:
    excel_path = write_excel_report(date, db, output)
    html_path = write_html_report(date, db, output)
    typer.echo(f"Wrote {excel_path}")
    typer.echo(f"Wrote {html_path}")


@app.command("dashboard")
def dashboard(
    date: str = typer.Option(..., "--date"),
    db: Path = typer.Option(...),
    output: Path = typer.Option(Path("web/public/data")),
) -> None:
    data_path = write_dashboard_data(date, db, output)
    typer.echo(f"Wrote dashboard data {data_path}")


@app.command("run-all")
def run_all(
    date: str = typer.Option(..., "--date"),
    db: Path = typer.Option(...),
    output: Path = typer.Option(...),
) -> None:
    DuckDBClient(db).init_db()
    run_id = ingest_raw_files(date, db)
    run_controls_engine(date, db)
    excel_path = write_excel_report(date, db, output)
    html_path = write_html_report(date, db, output)
    dashboard_path = write_dashboard_data(date, db)
    typer.echo(f"Run completed for {date}. run_id={run_id}")
    typer.echo(f"Wrote {excel_path}")
    typer.echo(f"Wrote {html_path}")
    typer.echo(f"Wrote dashboard data {dashboard_path}")


if __name__ == "__main__":
    app()
