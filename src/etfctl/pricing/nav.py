from __future__ import annotations


def calculate_indicative_nav(
    gross_basket_value: float,
    estimated_cash: float,
    balancing_amount: float,
    accrued_dividend: float,
    creation_unit_size: float,
) -> tuple[float, float]:
    net_basket_value = gross_basket_value + estimated_cash + balancing_amount + accrued_dividend
    return net_basket_value, net_basket_value / creation_unit_size

