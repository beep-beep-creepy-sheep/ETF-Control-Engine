from __future__ import annotations

from datetime import UTC, datetime
from itertools import count
from typing import Any

import pandas as pd


_PREFIX = {
    "MISSING_PRICE": "PRICE",
    "STALE_PRICE": "PRICE",
    "PRIMARY_PRICE_MISSING": "PRICE",
    "PRICE_VENDOR_DIFF": "PRICE",
    "FX_MISSING": "FX",
    "FX_STALE": "FX",
    "CURRENCY_MISMATCH": "FX",
    "LARGE_PREMIUM_DISCOUNT": "ETF",
    "CREATE_PRESSURE": "ETF",
    "REDEEM_PRESSURE": "ETF",
    "LARGE_WEIGHT_CHANGE": "BASKET",
    "NEW_COMPONENT": "BASKET",
    "REMOVED_COMPONENT": "BASKET",
    "MISSING_PCF_COMPONENT": "RECON",
    "MISSING_HOLDINGS_COMPONENT": "RECON",
    "QUANTITY_MISMATCH": "RECON",
    "IDENTIFIER_MISMATCH": "RECON",
    "CORPORATE_ACTION_MISMATCH": "CA",
    "DIVIDEND_CASH_COMPONENT_CHECK": "CA",
}


class ExceptionBuilder:
    """Creates normalized, rule-driven exception records."""

    def __init__(self, run_id: str, trade_date: str, etf_ticker: str, rules: dict[str, Any]) -> None:
        self.run_id = run_id
        self.trade_date = trade_date
        self.etf_ticker = etf_ticker
        self.rules = rules
        self._counter = count(1)

    def severity(self, exception_type: str) -> str:
        return self.rules.get("severity", {}).get(exception_type, "LOW")

    def build(
        self,
        exception_type: str,
        entity_type: str,
        entity_id: str,
        message: str,
        evidence: str,
    ) -> dict[str, object]:
        prefix = _PREFIX.get(exception_type, "RULE")
        return {
            "run_id": self.run_id,
            "trade_date": self.trade_date,
            "etf_ticker": self.etf_ticker,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "rule_id": f"{prefix}_{next(self._counter):03d}",
            "exception_type": exception_type,
            "severity": self.severity(exception_type),
            "message": message,
            "evidence": evidence,
            "created_at": datetime.now(UTC),
        }


def exceptions_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    columns = [
        "run_id",
        "trade_date",
        "etf_ticker",
        "entity_type",
        "entity_id",
        "rule_id",
        "exception_type",
        "severity",
        "message",
        "evidence",
        "created_at",
    ]
    return pd.DataFrame(rows, columns=columns)
