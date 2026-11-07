import os
import streamlit as st
import pandas as pd
import yfinance as yf
from google import genai

# Robust import for exposure_metrics
try:
    from analytics.exposure_metrics import compute_portfolio_analytics
except ModuleNotFoundError:
    from exposure_metrics import compute_portfolio_analytics

st.set_page_config(page_title="Zerodha AI Financial Intelligence", layout="wide")

st.title("📈 Zerodha AI Financial Intelligence Platform")
st.caption("Explainable Portfolio Analytics & Non-Discretionary Insights Engine")

SAMPLE_TICKERS = [
    "INFY", "TCS", "WIPRO", "HCLTECH",
    "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK",
    "RELIANCE", "ITC", "HINDUNILVR", "TATAMOTORS",
    "MARUTI", "SUNPHARMA"
]

@st.cache_data(ttl=300)
def fetch_live_price(symbol: str) -> float:
    """Fetch live Last Traded Price (LTP) from NSE via Yahoo Finance with local fallback."""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        price = ticker.fast_info.get('last_price') or ticker.fast_info.get('lastPrice')
        if price:
            return round(float(price), 2)
    except Exception:
        pass
    
    # Static fallback prices if market is closed or network times out
    fallback_prices = {
        "INFY": 1420.0, "TCS": 3550.0, "WIPRO": 450.0, "HCLTECH": 1500.0,
        "HDFCBANK": 1540.0, "ICICIBANK": 1050.0, "SBIN": 780.0, "KOTAKBANK": 1720.0,
        "RELIANCE": 2520.0, "ITC": 435.0, "HINDUNILVR": 2400.0, "TATAMOTORS": 680.0,
        "MARUTI": 11500.0, "SUNPHARMA": 1180.0
    }
    return fallback_prices.get(symbol, 1000.0)

def render_dashboard(metrics, is_simulation=False):
    """Render deterministic metric badges, holdings table, and the AI reasoning card."""
    # 1. Metric Badges
    col1, col2, col3, col4 = st.columns(4)
    label_pnl = "Hypothetical P&L" if is_simulation else "Unrealized P&L"
    col1.metric("Total Portfolio Value", f"₹{metrics['total_value']:,.2f}")
    col2.metric(label_pnl, f"₹{metrics['total_pnl']:,.2f}", f"{metrics['pnl_percentage']}%")
    col3.metric("Concentration (HHI)", f"{metrics['herfindahl_index']}", f"{metrics['volatility_flag']} RISK")
    col4.metric("Top Sector", f"{metrics['top_sector']}", f"{metrics['top_sector_pct']}% Exposure")

    st.divider()

    # 2. Holdings Breakdown Table
    with st.expander("🔍 View Calculated Allocation & Weights", expanded=False):
        display_df = metrics["df"][["symbol", "sector", "quantity", "avg_price", "current_price", "pnl", "weight"]].copy()
        display_df["weight"] = (display_df["weight"] * 100).round(2).astype(str) + "%"
        st.dataframe(display_df, use_container_width=True)

    # 3. AI Reasoning Layer
    mode_label = "Pre-Trade Simulation Review" if is_simulation else "Holdings Diagnostics"
    st.subheader(f"🤖 Explainable AI Reasoning Layer ({mode_label})")
    
    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

    button_key = "btn_sim" if is_simulation else "btn_real"
    if st.button("Generate Explainable Insights", key=button_key):
        if not api
