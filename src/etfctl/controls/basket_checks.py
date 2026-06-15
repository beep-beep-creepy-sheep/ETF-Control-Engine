from __future__ import annotations

from typing import Any

import pandas as pd


def drift_exceptions(
    basket: pd.DataFrame,
    prior_holdings: pd.DataFrame,
    builder: Any,
    rules: dict[str, Any],
) -> list[dict[str, object]]:
    exceptions: list[dict[str, object]] = []
    threshold = rules["thresholds"]["basket_drift_bps"]
    current = basket.set_index("ticker")["component_weight"].to_dict()
    prior = prior_holdings.set_index("ticker")["weight"].to_dict()

    for ticker, weight in current.items():
        if ticker not in prior:
            exceptions.append(builder.build("NEW_COMPONENT", "SECURITY", ticker, "New component versus prior holdings", f"weight={weight:.6f}"))
            continue
        change = (float(weight) - float(prior[ticker])) * 10000
        if abs(change) > threshold:
            exceptions.append(
                builder.build(
                    "LARGE_WEIGHT_CHANGE",
                    "SECURITY",
                    ticker,
                    f"Weight changed by {change:.1f} bps versus prior holdings",
                    f"current={weight:.6f}, prior={prior[ticker]:.6f}",
                )
            )

    for ticker in sorted(set(prior) - set(current)):
        exceptions.append(builder.build("REMOVED_COMPONENT", "SECURITY", ticker, "Prior component removed from current PCF basket", f"prior_weight={prior[ticker]:.6f}"))
    return exceptions

