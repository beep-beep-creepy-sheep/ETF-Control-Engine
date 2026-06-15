create table if not exists raw_pcf (
  trade_date date, etf_ticker varchar, creation_unit_size double, component_id varchar,
  ticker varchar, isin varchar, cusip varchar, sedol varchar, asset_type varchar,
  currency varchar, basket_quantity double, estimated_cash double, balancing_amount double,
  accrued_dividend double, transaction_fee double, cash_in_lieu_flag boolean
);

create table if not exists raw_holdings (
  trade_date date, etf_ticker varchar, ticker varchar, isin varchar, currency varchar,
  shares double, weight double
);

create table if not exists raw_prior_holdings (
  trade_date date, etf_ticker varchar, ticker varchar, isin varchar, currency varchar,
  shares double, weight double
);

create table if not exists raw_prices (
  trade_date date, ticker varchar, currency varchar, primary_price double, primary_time timestamp,
  secondary_price double, secondary_time timestamp, exchange_close double, exchange_close_time timestamp,
  manual_override double, manual_reason varchar
);

create table if not exists raw_fx (
  trade_date date, ccy varchar, fx_to_usd double, source varchar, last_update_time timestamp
);

create table if not exists raw_corporate_actions (
  effective_date date, ticker varchar, action_type varchar, ratio_old double, ratio_new double,
  cash_amount double, currency varchar
);

create table if not exists raw_etf_quotes (
  trade_date date, etf_ticker varchar, bid double, ask double, last double, quote_time timestamp
);

create table if not exists selected_prices (
  run_id varchar, trade_date date, ticker varchar, currency varchar, selected_price double,
  selected_source varchar, selected_time timestamp, price_age_hours double, price_status varchar,
  fallback_reason varchar
);

create table if not exists basket_valuation (
  run_id varchar, trade_date date, etf_ticker varchar, ticker varchar, currency varchar,
  basket_quantity double, selected_price double, fx_to_usd double, local_market_value double,
  usd_market_value double, component_weight double
);

create table if not exists etf_valuation (
  run_id varchar, trade_date date, etf_ticker varchar, gross_basket_value double,
  net_basket_value double, creation_unit_size double, indicative_nav double, bid double, ask double,
  mid_price double, premium_discount_bps double, create_edge_bps double, redeem_edge_bps double,
  arbitrage_signal varchar
);

create table if not exists control_exceptions (
  run_id varchar, trade_date date, etf_ticker varchar, entity_type varchar, entity_id varchar,
  rule_id varchar, exception_type varchar, severity varchar, message varchar, evidence varchar,
  created_at timestamp
);

create table if not exists run_audit (
  run_id varchar, trade_date date, file_type varchar, file_path varchar, file_hash varchar,
  row_count integer, status varchar, message varchar, created_at timestamp
);
