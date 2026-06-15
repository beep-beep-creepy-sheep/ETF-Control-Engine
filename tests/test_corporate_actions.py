from __future__ import annotations

import pandas as pd

from etfctl.controls.corporate_action_checks import corporate_action_exceptions
from etfctl.controls.rule_engine import ExceptionBuilder


def test_stock_split_quantity_mismatch_generates_corporate_action_exception() -> None:
    rules = {
        "thresholds": {"quantity_tolerance_pct": 0.5},
        "severity": {"CORPORATE_ACTION_MISMATCH": "HIGH"},
    }
    pcf = pd.DataFrame([{"ticker": "AAPL", "basket_quantity": 410, "accrued_dividend": 0}])
    holdings = pd.DataFrame([{"ticker": "AAPL", "shares": 400}])
    prior = pd.DataFrame([{"ticker": "AAPL", "shares": 205}])
    actions = pd.DataFrame(
        [{"ticker": "AAPL", "action_type": "SPLIT", "ratio_old": 1, "ratio_new": 2, "cash_amount": 0}]
    )
    builder = ExceptionBuilder("RUN", "2026-06-15", "GTEC", rules)
    exceptions = corporate_action_exceptions(pcf, holdings, prior, actions, builder, rules)
    assert exceptions[0]["exception_type"] == "CORPORATE_ACTION_MISMATCH"

