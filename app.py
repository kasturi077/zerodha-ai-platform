import os
import streamlit as st
import pandas as pd
from google import genai

# Robust import for exposure_metrics whether it's in analytics/ or root
try:
    from analytics.exposure_metrics import compute_portfolio_analytics
except ModuleNotFoundError:
    from exposure_metrics import compute_portfolio_analytics

st.set_page_config(page_title="Zerodha AI Financial Intelligence", layout="wide")

st.title("📈 Zerodha AI Financial Intelligence Platform")
st.caption("Explainable Portfolio Analytics & Non-Discretionary Insights Engine")

# --- File Uploader / Input Source ---
st.sidebar.header("📁 Portfolio Data Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload Portfolio CSV", 
    type=["csv"],
    help="CSV must contain: symbol, quantity, avg_price (or standard Zerodha Console format)"
)

# Determine data source: uploaded file, local file path, or built-in default dataframe
if uploaded_file is not None:
    data_source = uploaded_file
elif os.path.exists("data/sample_portfolio.csv"):
    data_source = "data/sample_portfolio.csv"
elif os.path.exists("sample_portfolio.csv"):
    data_source = "sample_portfolio.csv"
elif os.path.exists("data/sample_zerodha_console.csv"):
    data_source = "data/sample_zerodha_console.csv"
elif os.path.exists("sample_zerodha_console.csv"):
    data_source = "sample_zerodha_console.csv"
else:
    # Safe default: inline fallback data so the app always renders smoothly
    data_source = pd.DataFrame([
        {"symbol": "INFY", "sector": "Information Technology", "quantity": 50, "avg_price": 1400.0, "current_price": 1350.0},
        {"symbol": "TCS", "sector": "Information Technology", "quantity": 25, "avg_price": 3500.0, "current_price": 3420.0},
        {"symbol": "HDFCBANK", "sector": "Banking & Financials", "quantity": 40, "avg_price": 1480.0, "current_price": 1530.0},
        {"symbol": "RELIANCE", "sector": "Energy & Conglomerate", "quantity": 30, "avg_price": 2400.0, "current_price": 2480.0},
        {"symbol": "ITC", "sector": "Consumer Goods (FMCG)", "quantity": 100, "avg_price": 410.0, "current_price": 435.0}
    ])

try:
    metrics = compute_portfolio_analytics(data_source)
    
    if uploaded_file is not None:
        st.sidebar.success(f"Loaded: {uploaded_file.name}")
    else:
        st.sidebar.info("Using baseline demonstration portfolio.")

    # --- Holdings Preview ---
    with st.expander("🔍 View Raw Portfolio Holdings", expanded=False):
        st.dataframe(
            metrics["df"][["symbol", "sector", "quantity", "avg_price", "current_price", "pnl"]],
            use_container_width=True
        )

    # --- Metric KPI Badges ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Portfolio Value", f"₹{metrics['total_value']:,.2f}")
    col2.metric("Unrealized P&L", f"₹{metrics['total_pnl']:,.2f}", f"{metrics['pnl_percentage']}%")
    col3.metric("Concentration (HHI)", f"{metrics['herfindahl_index']}", f"{metrics['volatility_flag']} RISK")
    col4.metric("Top Sector", f"{metrics['top_sector']}", f"{metrics['top_sector_pct']}% Exposure")

    st.divider()

    # --- AI Reasoning Layer ---
    st.subheader("🤖 Explainable AI Reasoning Layer")
    
    # Retrieve key from Streamlit Cloud Secrets (or environment variable)
    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if st.button("Generate Explainable Insights"):
        if not api_key:
            st.error("Configuration Error: GEMINI_API_KEY is not set in Streamlit Cloud Secrets.")
        else:
            with st.spinner("Evaluating exposure thresholds, sector drift, and performance drivers..."):
                client = genai.Client(api_key=api_key)
                
                prompt = f"""
                You are the Zerodha Portfolio Intelligence Explainer.
                Analyze the following portfolio state using ONLY these computed metrics:
                - Total P&L: {metrics['pnl_percentage']}% (₹{metrics['total_pnl']})
                - Herfindahl Index (HHI): {metrics['herfindahl_index']} (Threshold: >2500 indicates elevated concentration risk)
                - Top Sector Exposure: {metrics['top_sector']} at {metrics['top_sector_pct']}% of portfolio
                - Primary Negative Contributor: {metrics['worst_performer']}

                STRICT GUIDELINES:
                1. Explain the primary cause of portfolio movement in objective, plain English.
                2. Highlight concentration risk or lack thereof based on the HHI score.
                3. DO NOT recommend buying, selling, or timing specific securities.
                4. Offer one structured review area under 'Risk Alert' or 'Diversification Opportunity'.
                5. End strictly with:
                'Disclaimer: Automated, non-discretionary insight for educational and review purposes only.'
                """
                
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )
                
                st.info(response.text)

except ValueError as ve:
    st.error(f"Data Schema Error: {ve}")
except Exception as e:
    st.error(f"Error processing portfolio: {e}")
