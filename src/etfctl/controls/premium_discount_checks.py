from __future__ import annotations

from typing import Any


def etf_exceptions(etf_row: dict[str, object], builder: Any, rules: dict[str, Any]) -> list[dict[str, object]]:
    exceptions: list[dict[str, object]] = []
    threshold = rules["thresholds"]["large_premium_discount_bps"]
    bps = float(etf_row["premium_discount_bps"])
    if abs(bps) > threshold:
        direction = "above" if bps > 0 else "below"
        exceptions.append(
            builder.build(
                "LARGE_PREMIUM_DISCOUNT",
                "ETF",
                str(etf_row["etf_ticker"]),
                f"ETF mid price is {abs(bps):.1f} bps {direction} indicative NAV",
                f"mid={etf_row['mid_price']}, indicative_nav={etf_row['indicative_nav']}",
            )
        )
    return exceptions

