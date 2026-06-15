from __future__ import annotations

from typing import Any


def premium_discount_bps(mid_price: float, indicative_nav: float) -> float:
    return (mid_price / indicative_nav - 1) * 10000


def arbitrage_edges(bid: float, ask: float, indicative_nav: float, rules: dict[str, Any]) -> tuple[float, float, str]:
    arb = rules["arbitrage"]
    create_edge = ((bid - indicative_nav) / indicative_nav) * 10000 - arb["create_cost_bps"]
    redeem_edge = ((indicative_nav - ask) / indicative_nav) * 10000 - arb["redeem_cost_bps"]
    if create_edge > arb["min_edge_bps"]:
        signal = "CREATE_PRESSURE"
    elif redeem_edge > arb["min_edge_bps"]:
        signal = "REDEEM_PRESSURE"
    else:
        signal = "WITHIN_COST_BAND"
    return create_edge, redeem_edge, signal

