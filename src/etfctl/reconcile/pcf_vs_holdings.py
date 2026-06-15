from __future__ import annotations

from typing import Any

import pandas as pd


def pcf_vs_holdings_exceptions(
    pcf: pd.DataFrame,
    holdings: pd.DataFrame,
    builder: Any,
    rules: dict[str, Any],
) -> list[dict[str, object]]:
    exceptions: list[dict[str, object]] = []
    tolerance_pct = rules["thresholds"]["quantity_tolerance_pct"]
    pcf_by_ticker = pcf.set_index("ticker").to_dict("index")
    holding_by_ticker = holdings.set_index("ticker").to_dict("index")

    for ticker, pcf_row in pcf_by_ticker.items():
        holding_row = holding_by_ticker.get(ticker)
        if holding_row is None:
            exceptions.append(builder.build("MISSING_HOLDINGS_COMPONENT", "SECURITY", ticker, "PCF component missing from holdings", "ticker not present in holdings"))
            continue
        expected = float(pcf_row["basket_quantity"])
        actual = float(holding_row["shares"])
        if expected and abs(actual - expected) / expected * 100 > tolerance_pct:
            exceptions.append(
                builder.build(
                    "QUANTITY_MISMATCH",
                    "SECURITY",
                    ticker,
                    "PCF basket quantity differs from holdings shares",
                    f"pcf_quantity={expected}, holdings_shares={actual}",
                )
            )
        if str(pcf_row.get("isin")) != str(holding_row.get("isin")):
            exceptions.append(builder.build("IDENTIFIER_MISMATCH", "SECURITY", ticker, "ISIN mismatch between PCF and holdings", f"pcf={pcf_row.get('isin')}, holdings={holding_row.get('isin')}"))

    for ticker in sorted(set(holding_by_ticker) - set(pcf_by_ticker)):
        exceptions.append(builder.build("MISSING_PCF_COMPONENT", "SECURITY", ticker, "Holdings component missing from PCF basket", "ticker not present in PCF"))
    return exceptions

