from __future__ import annotations

from typing import Any

import pandas as pd


def get_fx_rate(ccy: str, fx: pd.DataFrame, as_of: str, rules: dict[str, Any]) -> tuple[float | None, str]:
    if ccy == "USD":
        return 1.0, "OK"
    match = fx[fx["ccy"] == ccy]
    if match.empty:
        return None, "FX_MISSING"
    row = match.iloc[0]
    age = (pd.Timestamp(as_of) - pd.Timestamp(row["last_update_time"])).total_seconds() / 3600
    if age > rules["fx"]["stale_fx_hours"]:
        return float(row["fx_to_usd"]), "FX_STALE"
    return float(row["fx_to_usd"]), "OK"


def fx_exceptions(pcf: pd.DataFrame, selected: pd.DataFrame, fx: pd.DataFrame, builder: Any, rules: dict[str, Any], as_of: str) -> list[dict[str, object]]:
    exceptions: list[dict[str, object]] = []
    selected_currency = selected.set_index("ticker")["currency"].to_dict()
    for _, row in pcf.iterrows():
        ticker = row["ticker"]
        ccy = row["currency"]
        rate, status = get_fx_rate(ccy, fx, as_of, rules)
        if selected_currency.get(ticker) and selected_currency[ticker] != ccy:
            exceptions.append(
                builder.build(
                    "CURRENCY_MISMATCH",
                    "SECURITY",
                    ticker,
                    "Security price currency differs from PCF component currency",
                    f"pcf={ccy}, price={selected_currency[ticker]}",
                )
            )
        if status == "FX_MISSING":
            exceptions.append(builder.build("FX_MISSING", "SECURITY", ticker, f"Missing {ccy}/USD FX rate", f"ccy={ccy}"))
        if status == "FX_STALE":
            exceptions.append(
                builder.build("FX_STALE", "SECURITY", ticker, f"{ccy}/USD FX rate is stale", f"fx_to_usd={rate}")
            )
    return exceptions

