from __future__ import annotations

import pandas as pd

from etfctl.controls.rule_engine import ExceptionBuilder
from etfctl.pricing.price_waterfall import price_exceptions, select_price


RULES = {
    "pricing": {"stale_price_hours": {"US": 24, "DEFAULT": 24}, "price_vendor_diff_bps": 20},
    "severity": {"MISSING_PRICE": "HIGH", "STALE_PRICE": "MEDIUM", "PRIMARY_PRICE_MISSING": "LOW"},
}


def test_selected_price_uses_primary_when_valid() -> None:
    row = {
        "trade_date": "2026-06-15",
        "ticker": "AAPL",
        "currency": "USD",
        "primary_price": 200,
        "primary_time": "2026-06-15 15:00:00",
        "secondary_price": 199,
        "secondary_time": "2026-06-15 15:00:00",
        "exchange_close": 198,
        "exchange_close_time": "2026-06-15 15:00:00",
        "manual_override": None,
    }
    selected = select_price(row, RULES, "US", "2026-06-15 16:00:00")
    assert selected["selected_source"] == "PRIMARY"
    assert selected["selected_price"] == 200


def test_selected_price_falls_back_to_secondary_when_primary_missing() -> None:
    row = {
        "trade_date": "2026-06-15",
        "ticker": "ASML",
        "currency": "EUR",
        "primary_price": None,
        "primary_time": None,
        "secondary_price": 700,
        "secondary_time": "2026-06-15 15:00:00",
        "exchange_close": 698,
        "exchange_close_time": "2026-06-15 15:00:00",
        "manual_override": None,
    }
    selected = select_price(row, RULES, "US", "2026-06-15 16:00:00")
    assert selected["selected_source"] == "SECONDARY"
    assert selected["fallback_reason"] == "PRIMARY_PRICE_MISSING"


def test_missing_price_generates_high_severity_exception() -> None:
    prices = pd.DataFrame(
        [
            {
                "trade_date": "2026-06-15",
                "ticker": "NVDA",
                "currency": "USD",
                "primary_price": None,
                "secondary_price": None,
                "exchange_close": None,
            }
        ]
    )
    selected = pd.DataFrame(
        [{"ticker": "NVDA", "price_status": "MISSING", "fallback_reason": "NO_VALID_PRICE"}]
    )
    builder = ExceptionBuilder("RUN", "2026-06-15", "GTEC", RULES)
    exceptions = price_exceptions(prices, selected, builder, RULES)
    assert exceptions[0]["exception_type"] == "MISSING_PRICE"
    assert exceptions[0]["severity"] == "HIGH"


def test_stale_price_generates_exception() -> None:
    prices = pd.DataFrame([{"ticker": "SAP", "primary_price": 120, "secondary_price": None}])
    selected = pd.DataFrame(
        [{"ticker": "SAP", "price_status": "STALE", "fallback_reason": "STALE_PRIMARY", "price_age_hours": 54}]
    )
    builder = ExceptionBuilder("RUN", "2026-06-15", "GTEC", RULES)
    exceptions = price_exceptions(prices, selected, builder, RULES)
    assert exceptions[0]["exception_type"] == "STALE_PRICE"

