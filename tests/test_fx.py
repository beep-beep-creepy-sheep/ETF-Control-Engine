from __future__ import annotations

import pandas as pd

from etfctl.controls.rule_engine import ExceptionBuilder
from etfctl.pricing.fx import fx_exceptions


def test_non_usd_security_with_missing_fx_generates_fx_missing() -> None:
    rules = {"fx": {"stale_fx_hours": 24}, "severity": {"FX_MISSING": "HIGH"}}
    pcf = pd.DataFrame([{"ticker": "7203", "currency": "JPY"}])
    selected = pd.DataFrame([{"ticker": "7203", "currency": "JPY"}])
    fx = pd.DataFrame([{"ccy": "USD", "fx_to_usd": 1.0, "last_update_time": "2026-06-15 16:00:00"}])
    builder = ExceptionBuilder("RUN", "2026-06-15", "GTEC", rules)
    exceptions = fx_exceptions(pcf, selected, fx, builder, rules, "2026-06-15 16:00:00")
    assert exceptions[0]["exception_type"] == "FX_MISSING"

