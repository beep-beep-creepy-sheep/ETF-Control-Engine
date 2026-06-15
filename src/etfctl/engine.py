from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from etfctl.config import AS_OF_TIMESTAMP, load_calendars, load_rules
from etfctl.controls.basket_checks import drift_exceptions
from etfctl.controls.corporate_action_checks import corporate_action_exceptions
from etfctl.controls.premium_discount_checks import etf_exceptions
from etfctl.controls.rule_engine import ExceptionBuilder, exceptions_frame
from etfctl.pricing.arbitrage import arbitrage_edges, premium_discount_bps
from etfctl.pricing.fx import fx_exceptions
from etfctl.pricing.nav import calculate_indicative_nav
from etfctl.pricing.price_waterfall import build_selected_prices, price_exceptions
from etfctl.pricing.valuation import basket_cash_terms, value_basket
from etfctl.reconcile.pcf_vs_holdings import pcf_vs_holdings_exceptions
from etfctl.storage.duckdb_client import DuckDBClient


def _latest_run_id(client: DuckDBClient, trade_date: str) -> str:
    frame = client.read_df(
        "select run_id from run_audit where trade_date = ? order by created_at desc limit 1",
        [trade_date],
    )
    if frame.empty:
        return f"RUN-{trade_date}-{uuid4().hex[:8]}"
    return str(frame.iloc[0]["run_id"])


def run_controls(trade_date: str, db_path: str | Path) -> str:
    """Run price, FX, valuation, reconciliation, and ETF-level controls."""
    client = DuckDBClient(db_path)
    client.init_db()
    run_id = _latest_run_id(client, trade_date)
    rules = load_rules()
    calendars = load_calendars()

    pcf = client.read_df("select * from raw_pcf where trade_date = ?", [trade_date])
    holdings = client.read_df("select * from raw_holdings where trade_date = ?", [trade_date])
    prices = client.read_df("select * from raw_prices where trade_date = ?", [trade_date])
    fx = client.read_df("select * from raw_fx where trade_date = ?", [trade_date])
    corporate_actions = client.read_df(
        "select * from raw_corporate_actions where effective_date = ?", [trade_date]
    )
    quotes = client.read_df("select * from raw_etf_quotes where trade_date = ?", [trade_date])
    prior_holdings = client.read_df("select * from raw_prior_holdings order by trade_date desc")

    if pcf.empty:
        raise ValueError(f"No PCF rows loaded for {trade_date}. Run etfctl ingest first.")
    etf_ticker = str(pcf.iloc[0]["etf_ticker"])
    builder = ExceptionBuilder(run_id, trade_date, etf_ticker, rules)

    selected = build_selected_prices(prices, rules, calendars, AS_OF_TIMESTAMP)
    selected.insert(0, "run_id", run_id)
    basket = value_basket(run_id, trade_date, pcf, selected, fx, rules, AS_OF_TIMESTAMP)

    estimated_cash, balancing_amount, accrued_dividend, creation_unit_size = basket_cash_terms(pcf)
    gross_value = float(basket["usd_market_value"].sum())
    net_value, indicative_nav = calculate_indicative_nav(
        gross_value,
        estimated_cash,
        balancing_amount,
        accrued_dividend,
        creation_unit_size,
    )
    quote = quotes.iloc[0]
    mid = (float(quote["bid"]) + float(quote["ask"])) / 2
    premium_bps = premium_discount_bps(mid, indicative_nav)
    create_edge, redeem_edge, arb_signal = arbitrage_edges(
        float(quote["bid"]), float(quote["ask"]), indicative_nav, rules
    )
    etf_row = {
        "run_id": run_id,
        "trade_date": trade_date,
        "etf_ticker": etf_ticker,
        "gross_basket_value": gross_value,
        "net_basket_value": net_value,
        "creation_unit_size": creation_unit_size,
        "indicative_nav": indicative_nav,
        "bid": float(quote["bid"]),
        "ask": float(quote["ask"]),
        "mid_price": mid,
        "premium_discount_bps": premium_bps,
        "create_edge_bps": create_edge,
        "redeem_edge_bps": redeem_edge,
        "arbitrage_signal": arb_signal,
    }
    etf = pd.DataFrame([etf_row])

    exceptions: list[dict[str, object]] = []
    exceptions.extend(price_exceptions(prices, selected, builder, rules))
    exceptions.extend(fx_exceptions(pcf, selected, fx, builder, rules, AS_OF_TIMESTAMP))
    exceptions.extend(etf_exceptions(etf_row, builder, rules))
    exceptions.extend(drift_exceptions(basket, prior_holdings, builder, rules))
    exceptions.extend(pcf_vs_holdings_exceptions(pcf, holdings, builder, rules))
    exceptions.extend(
        corporate_action_exceptions(pcf, holdings, prior_holdings, corporate_actions, builder, rules)
    )
    if arb_signal in {"CREATE_PRESSURE", "REDEEM_PRESSURE"}:
        exceptions.append(
            builder.build(
                arb_signal,
                "ETF",
                etf_ticker,
                "ETF quote is outside the simplified cost band; investigate create/redeem pressure",
                f"create_edge_bps={create_edge:.2f}, redeem_edge_bps={redeem_edge:.2f}",
            )
        )

    client.replace_runtime_table("selected_prices", trade_date, selected)
    client.replace_runtime_table("basket_valuation", trade_date, basket)
    client.replace_runtime_table("etf_valuation", trade_date, etf)
    client.replace_runtime_table("control_exceptions", trade_date, exceptions_frame(exceptions))

    client.append_df(
        "run_audit",
        pd.DataFrame(
            [
                {
                    "run_id": run_id,
                    "trade_date": trade_date,
                    "file_type": "controls",
                    "file_path": "",
                    "file_hash": "",
                    "row_count": len(exceptions),
                    "status": "COMPLETED",
                    "message": "controls executed",
                    "created_at": datetime.now(UTC),
                }
            ]
        ),
    )
    return run_id
