from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PCFRow(StrictModel):
    trade_date: str
    etf_ticker: str
    creation_unit_size: float
    component_id: str
    ticker: str
    isin: str | None = None
    cusip: str | None = None
    sedol: str | None = None
    asset_type: str
    currency: str
    basket_quantity: float
    estimated_cash: float
    balancing_amount: float
    accrued_dividend: float
    transaction_fee: float
    cash_in_lieu_flag: bool


class HoldingsRow(StrictModel):
    trade_date: str
    etf_ticker: str
    ticker: str
    isin: str
    currency: str
    shares: float
    weight: float


class PriceRow(StrictModel):
    trade_date: str
    ticker: str
    currency: str
    primary_price: float | None = None
    primary_time: str | None = None
    secondary_price: float | None = None
    secondary_time: str | None = None
    exchange_close: float | None = None
    exchange_close_time: str | None = None
    manual_override: float | None = None
    manual_reason: str | None = None


class FXRow(StrictModel):
    trade_date: str
    ccy: str
    fx_to_usd: float
    source: str
    last_update_time: str


class CorporateActionRow(StrictModel):
    effective_date: str
    ticker: str
    action_type: str
    ratio_old: float
    ratio_new: float
    cash_amount: float
    currency: str


class ETFQuoteRow(StrictModel):
    trade_date: str
    etf_ticker: str
    bid: float
    ask: float
    last: float
    quote_time: str

