from __future__ import annotations

from typing import Any

import pandas as pd

from etfctl.pricing.fx import get_fx_rate


def value_basket(
    run_id: str,
    trade_date: str,
    pcf: pd.DataFrame,
    selected_prices: pd.DataFrame,
    fx: pd.DataFrame,
    rules: dict[str, Any],
    as_of: str,
) -> pd.DataFrame:
    price_map = selected_prices.set_index("ticker").to_dict("index")
    rows: list[dict[str, object]] = []
    total = 0.0
    for _, row in pcf.iterrows():
        selected = price_map.get(row["ticker"], {})
        price = selected.get("selected_price")
        rate, _ = get_fx_rate(row["currency"], fx, as_of, rules)
        local_mv = float(row["basket_quantity"]) * float(price) if pd.notna(price) else 0.0
        usd_mv = local_mv * rate if rate is not None else 0.0
        total += usd_mv
        rows.append(
            {
                "run_id": run_id,
                "trade_date": trade_date,
                "etf_ticker": row["etf_ticker"],
                "ticker": row["ticker"],
                "currency": row["currency"],
                "basket_quantity": float(row["basket_quantity"]),
                "selected_price": price,
                "fx_to_usd": rate,
                "local_market_value": local_mv,
                "usd_market_value": usd_mv,
                "component_weight": 0.0,
            }
        )
    for item in rows:
        item["component_weight"] = item["usd_market_value"] / total if total else 0.0
    return pd.DataFrame(rows)


def basket_cash_terms(pcf: pd.DataFrame) -> tuple[float, float, float, float]:
    first = pcf.iloc[0]
    return (
        float(first["estimated_cash"]),
        float(first["balancing_amount"]),
        float(first["accrued_dividend"]),
        float(first["creation_unit_size"]),
    )

