from __future__ import annotations

from typing import Any

import pandas as pd


def _valid_price(value: object) -> bool:
    return pd.notna(value) and float(value) > 0


def _age_hours(value: object, as_of: pd.Timestamp) -> float | None:
    if pd.isna(value) or value in ("", None):
        return None
    return round((as_of - pd.Timestamp(value)).total_seconds() / 3600, 4)


def select_price(row: pd.Series | dict[str, Any], rules: dict[str, Any], region: str, as_of: str) -> dict[str, object]:
    """Apply the configured ETF operations price waterfall for one security."""
    item = dict(row)
    as_of_ts = pd.Timestamp(as_of)
    stale_hours = rules["pricing"]["stale_price_hours"].get(
        region, rules["pricing"]["stale_price_hours"]["DEFAULT"]
    )

    candidates = [
        ("MANUAL_OVERRIDE", item.get("manual_override"), item.get("primary_time"), "manual override"),
        ("PRIMARY", item.get("primary_price"), item.get("primary_time"), "primary vendor"),
        ("SECONDARY", item.get("secondary_price"), item.get("secondary_time"), "secondary vendor"),
        ("EXCHANGE_CLOSE", item.get("exchange_close"), item.get("exchange_close_time"), "exchange close"),
    ]

    fallback_reason = ""
    if not _valid_price(item.get("primary_price")) and _valid_price(item.get("secondary_price")):
        fallback_reason = "PRIMARY_PRICE_MISSING"

    for source, price, timestamp, reason in candidates:
        if not _valid_price(price):
            continue
        age = _age_hours(timestamp, as_of_ts)
        is_stale = age is not None and age > stale_hours
        if source == "PRIMARY" and is_stale:
            continue
        if source != "MANUAL_OVERRIDE" and is_stale:
            continue
        return {
            "trade_date": item["trade_date"],
            "ticker": item["ticker"],
            "currency": item["currency"],
            "selected_price": float(price),
            "selected_source": source,
            "selected_time": timestamp,
            "price_age_hours": age,
            "price_status": "OK",
            "fallback_reason": fallback_reason or reason,
        }

    stale_candidates = [
        (source, price, timestamp, reason)
        for source, price, timestamp, reason in candidates
        if _valid_price(price)
    ]
    if stale_candidates:
        source, price, timestamp, reason = stale_candidates[0]
        age = _age_hours(timestamp, as_of_ts)
        return {
            "trade_date": item["trade_date"],
            "ticker": item["ticker"],
            "currency": item["currency"],
            "selected_price": float(price),
            "selected_source": source,
            "selected_time": timestamp,
            "price_age_hours": age,
            "price_status": "STALE",
            "fallback_reason": f"STALE_{reason.upper().replace(' ', '_')}",
        }

    return {
        "trade_date": item["trade_date"],
        "ticker": item["ticker"],
        "currency": item["currency"],
        "selected_price": None,
        "selected_source": "NONE",
        "selected_time": None,
        "price_age_hours": None,
        "price_status": "MISSING",
        "fallback_reason": "NO_VALID_PRICE",
    }


def build_selected_prices(
    prices: pd.DataFrame,
    rules: dict[str, Any],
    calendars: dict[str, Any],
    as_of: str,
) -> pd.DataFrame:
    region_map = calendars.get("ticker_region", {})
    rows = [
        select_price(row, rules, region_map.get(row["ticker"], "DEFAULT"), as_of)
        for _, row in prices.iterrows()
    ]
    return pd.DataFrame(rows)


def price_exceptions(
    prices: pd.DataFrame,
    selected: pd.DataFrame,
    builder: Any,
    rules: dict[str, Any],
) -> list[dict[str, object]]:
    exceptions: list[dict[str, object]] = []
    selected_by_ticker = selected.set_index("ticker")
    diff_threshold = rules["pricing"]["price_vendor_diff_bps"]

    for _, row in prices.iterrows():
        ticker = row["ticker"]
        selected_row = selected_by_ticker.loc[ticker]
        if selected_row["price_status"] == "MISSING":
            exceptions.append(
                builder.build("MISSING_PRICE", "SECURITY", ticker, "No valid market price available", str(row.to_dict()))
            )
        if selected_row["price_status"] == "STALE":
            exceptions.append(
                builder.build(
                    "STALE_PRICE",
                    "SECURITY",
                    ticker,
                    "Selected price is older than configured stale threshold",
                    f"age_hours={selected_row['price_age_hours']}",
                )
            )
        if selected_row["fallback_reason"] == "PRIMARY_PRICE_MISSING":
            exceptions.append(
                builder.build(
                    "PRIMARY_PRICE_MISSING",
                    "SECURITY",
                    ticker,
                    "Primary price missing; secondary price selected",
                    str(row.to_dict()),
                )
            )
        if _valid_price(row.get("primary_price")) and _valid_price(row.get("secondary_price")):
            bps = abs(float(row["primary_price"]) / float(row["secondary_price"]) - 1) * 10000
            if bps > diff_threshold:
                exceptions.append(
                    builder.build(
                        "PRICE_VENDOR_DIFF",
                        "SECURITY",
                        ticker,
                        "Primary and secondary vendor prices differ beyond threshold",
                        f"vendor_diff_bps={bps:.2f}",
                    )
                )
    return exceptions
