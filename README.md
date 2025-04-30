# High‑Growth / Turnaround US Stocks Dataset

This repository auto-refreshes **every Monday 06:00 UTC** (and on manual dispatch) to produce:

* `high_growth_turnaround_us_stocks.csv`
* `high_growth_turnaround_us_stocks.xlsx`

### How it works

1. **Finviz** screener grabs tickers with 5‑year sales growth > 20 %.
2. **yFinance** pulls the last 3 fiscal years of statements.
3. Script keeps companies with:
   * 3‑year revenue CAGR ≥ 20 %
   * Market cap between \$100 M and \$100 B
   * GAAP net-income has turned positive (or within ±\$20 M of break-even).
4. Files are committed back to `main` by `git-auto-commit-action`.
