from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
AS_OF_TIMESTAMP = "2026-06-15 16:00:00"


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_rules() -> dict[str, Any]:
    return load_yaml(ROOT / "config" / "rules.yaml")


def load_calendars() -> dict[str, Any]:
    return load_yaml(ROOT / "config" / "calendars.yaml")


def raw_path(name: str, trade_date: str) -> Path:
    return ROOT / "data" / "raw" / f"{name}_{trade_date}.csv"


def prior_holdings_path(trade_date: str) -> Path:
    # The sample run date is 2026-06-15 with a prior-day fixture dated 2026-06-14.
    if trade_date == "2026-06-15":
        return ROOT / "data" / "raw" / "prior_holdings_2026-06-14.csv"
    return ROOT / "data" / "raw" / f"prior_holdings_{trade_date}.csv"

