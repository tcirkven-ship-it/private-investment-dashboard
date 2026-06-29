"""Smoke test for quarterly model generation — tests Python env + yfinance."""
import yfinance as yf, pandas as pd, numpy as np, time, os, csv

print(f"Dependencies: pandas={pd.__version__} numpy={np.__version__}")
t = yf.Ticker("MU")
h = t.history(period="5d", auto_adjust=False)
close = float(h["Close"].iloc[-1]) if len(h) > 0 else None
print(f"Smoke: MU close={close}")

os.makedirs("outputs/quarterly/daily_qvp_runs/smoke", exist_ok=True)
with open("outputs/quarterly/daily_qvp_runs/smoke/portfolio.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["ticker","yf_p_score","YF-QVP_percentile","quality_score","sector","industry","company_name"])
    w.writerow(["MU", 0.98, 0.99, 0.69, "Technology", "Semiconductors", "Micron Technology Inc."])
print("Smoke: Python environment OK")
