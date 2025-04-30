#!/usr/bin/env python3
\"\"\"Build updated high_growth_turnaround US stocks dataset.

Steps:
  1. Use Finviz screener API to pull tickers with 5‑year sales growth > 20%.
  2. Pull financial statements via yfinance.
  3. Compute 3‑year revenue CAGR, net‑income trend; detect sign change (loss→profit).
  4. Keep companies with CAGR ≥ 20 %, market cap 0.1–100 B USD, and either
     a) GAAP net‑income turned positive in trailing 4 quarters, or
     b) GAAP loss within −20 M to 0 M (near break‑even).
  5. Save results to CSV and Excel.

Run locally:
    pip install pandas yfinance finvizfinance tqdm
\"\"\"
import pandas as pd, numpy as np
from datetime import datetime
from finvizfinance.screener.overview import Overview
import yfinance as yf
from tqdm import tqdm

MIN_SALES_CAGR = 20          # %
MIN_MARKET_CAP = 100         # $M
MAX_MARKET_CAP = 100000      # $M
TODAY = datetime.utcnow().strftime("%Y-%m-%d")

def query_finviz():
    filters = [
        "sales5years%3Over20",
        "cap_smallover",
        "cap_megaUnder"
    ]
    scr = Overview()
    scr.set_filter(filters=filters)
    df_raw = scr.screener_view()
    return df_raw[\"Ticker\"].tolist()

def fetch_metrics(ticker):
    t = yf.Ticker(ticker)
    try:
        fin = t.financials.T
        rev = fin[\"Total Revenue\"].tail(3) / 1e6
        ni  = fin[\"Net Income\"].tail(3) / 1e6
        ocf = t.cashflow.T[\"Total Cash From Operating Activities\"].iloc[-1] / 1e6
        bs  = t.balance_sheet.T
        debt = bs[\"Total Debt\"].iloc[-1] / 1e6
        eq   = bs[\"Total Stockholder Equity\"].iloc[-1] / 1e6
        mcap = t.info.get(\"marketCap\", np.nan) / 1e6
    except Exception as e:
        print(\"skip\", ticker, e)
        return None

    if len(rev) < 3 or len(ni) < 3:
        return None

    cagr = ((rev.iloc[-1] / rev.iloc[0]) ** (1/2) - 1) * 100 if rev.iloc[0] > 0 else np.nan
    ni_cagr = ((abs(ni.iloc[-1]) / abs(ni.iloc[0])) ** (1/2) - 1) * 100 if ni.iloc[0] != 0 else np.nan
    sign_change = (ni.iloc[0] < 0) and (ni.iloc[-1] > 0)

    return {
        \"Ticker\": ticker,
        \"Rev_2022($M)\": rev.iloc[0],
        \"Rev_2023($M)\": rev.iloc[1],
        \"Rev_2024($M)\": rev.iloc[2],
        \"NI_2022($M)\": ni.iloc[0],
        \"NI_2023($M)\": ni.iloc[1],
        \"NI_2024($M)\": ni.iloc[2],
        \"OCF_2024($M)\": ocf,
        \"Debt/Equity\": debt / eq if eq != 0 else np.nan,
        \"RevCAGR_3y(%)\": cagr,
        \"NICAGR_3y(%)\": ni_cagr,
        \"NI_sign_change\": sign_change,
        \"MarketCap($M)\": mcap,
    }

def main():
    tickers = query_finviz()
    rows = []
    for tk in tqdm(tickers, desc=\"Pulling data\"):
        m = fetch_metrics(tk)
        if m:
            rows.append(m)
    df = pd.DataFrame(rows)
    df = df[
        (df[\"RevCAGR_3y(%)\"] >= MIN_SALES_CAGR) &
        (df[\"MarketCap($M)\"] >= MIN_MARKET_CAP) &
        (df[\"MarketCap($M)\"] <= MAX_MARKET_CAP) &
        (
            df[\"NI_sign_change\"] |
            (df[\"NI_2024($M)\"] > 0) |
            df[\"NI_2024($M)\"].between(-20, 0)
        )
    ]
    df.to_csv(\"high_growth_turnaround_us_stocks.csv\", index=False)
    df.to_excel(\"high_growth_turnaround_us_stocks.xlsx\", index=False)
    print(f\"Saved {len(df)} tickers on {TODAY}\")

if __name__ == \"__main__\":
    main()
