from __future__ import annotations

import pandas as pd

from etfctl.controls.basket_checks import drift_exceptions
from etfctl.controls.rule_engine import ExceptionBuilder
from etfctl.reconcile.pcf_vs_holdings import pcf_vs_holdings_exceptions


def test_large_basket_weight_change_generates_exception() -> None:
    rules = {
        "thresholds": {"basket_drift_bps": 25},
        "severity": {"LARGE_WEIGHT_CHANGE": "MEDIUM"},
    }
    basket = pd.DataFrame([{"ticker": "AAPL", "component_weight": 0.30}])
    prior = pd.DataFrame([{"ticker": "AAPL", "weight": 0.20}])
    builder = ExceptionBuilder("RUN", "2026-06-15", "GTEC", rules)
    exceptions = drift_exceptions(basket, prior, builder, rules)
    assert exceptions[0]["exception_type"] == "LARGE_WEIGHT_CHANGE"


def test_pcf_component_missing_from_holdings_generates_exception() -> None:
    rules = {
        "thresholds": {"quantity_tolerance_pct": 0.5},
        "severity": {"MISSING_HOLDINGS_COMPONENT": "HIGH"},
    }
    pcf = pd.DataFrame([{"ticker": "NVDA", "basket_quantity": 180, "isin": "US67066G1040"}])
    holdings = pd.DataFrame(columns=["ticker", "shares", "isin"])
    builder = ExceptionBuilder("RUN", "2026-06-15", "GTEC", rules)
    exceptions = pcf_vs_holdings_exceptions(pcf, holdings, builder, rules)
    assert exceptions[0]["exception_type"] == "MISSING_HOLDINGS_COMPONENT"

