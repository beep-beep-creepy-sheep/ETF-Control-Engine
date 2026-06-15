from __future__ import annotations


def ticker_region(ticker: str, calendars: dict[str, object]) -> str:
    return dict(calendars.get("ticker_region", {})).get(ticker, "DEFAULT")

