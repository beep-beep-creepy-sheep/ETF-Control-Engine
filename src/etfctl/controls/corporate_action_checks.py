from __future__ import annotations

from typing import Any

import pandas as pd


def corporate_action_exceptions(
    pcf: pd.DataFrame,
    holdings: pd.DataFrame,
    prior_holdings: pd.DataFrame,
    corporate_actions: pd.DataFrame,
    builder: Any,
    rules: dict[str, Any],
) -> list[dict[str, object]]:
    exceptions: list[dict[str, object]] = []
    tolerance_pct = rules["thresholds"]["quantity_tolerance_pct"]
    pcf_qty = pcf.set_index("ticker")["basket_quantity"].to_dict()
    hold_qty = holdings.set_index("ticker")["shares"].to_dict()
    prior_qty = prior_holdings.set_index("ticker")["shares"].to_dict()

    for _, action in corporate_actions.iterrows():
        ticker = action["ticker"]
        if action["action_type"] == "SPLIT" and ticker in prior_qty:
            expected = float(prior_qty[ticker]) * float(action["ratio_new"]) / float(action["ratio_old"])
            for label, quantities in (("PCF", pcf_qty), ("holdings", hold_qty)):
                actual = quantities.get(ticker)
                if actual is None:
                    continue
                diff_pct = abs(float(actual) - expected) / expected * 100 if expected else 0.0
                if diff_pct > tolerance_pct:
                    exceptions.append(
                        builder.build(
                            "CORPORATE_ACTION_MISMATCH",
                            "SECURITY",
                            ticker,
                            "Split-adjusted quantity does not match expected ratio",
                            f"{label}_quantity={actual}, expected={expected:.4f}, diff_pct={diff_pct:.4f}",
                        )
                    )
        if action["action_type"] == "DIVIDEND":
            accrued = float(pcf["accrued_dividend"].iloc[0])
            expected_cash = float(pcf_qty.get(ticker, 0.0)) * float(action["cash_amount"])
            if expected_cash > 0 and accrued < expected_cash * 0.25:
                exceptions.append(
                    builder.build(
                        "DIVIDEND_CASH_COMPONENT_CHECK",
                        "SECURITY",
                        ticker,
                        "Dividend cash amount does not appear fully reflected in accrued dividend",
                        f"expected_cash={expected_cash:.2f}, accrued_dividend={accrued:.2f}",
                    )
                )
    return exceptions

