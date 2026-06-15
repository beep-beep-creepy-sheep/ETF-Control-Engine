from __future__ import annotations

import pytest

from etfctl.pricing.arbitrage import arbitrage_edges, premium_discount_bps


def test_premium_discount_bps_calculation_is_correct() -> None:
    assert premium_discount_bps(101, 100) == pytest.approx(100)


def test_create_redeem_arbitrage_signal_is_correct() -> None:
    rules = {"arbitrage": {"create_cost_bps": 12, "redeem_cost_bps": 12, "min_edge_bps": 5}}
    create_edge, redeem_edge, signal = arbitrage_edges(101, 101.2, 100, rules)
    assert create_edge == 88
    assert redeem_edge < 0
    assert signal == "CREATE_PRESSURE"
