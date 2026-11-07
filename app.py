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

# Pre-defined list of common stocks for easy selection in sandbox
SAMPLE_TICKERS = [
    "INFY", "TCS", "WIPRO", "HCLTECH",
    "HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK",
    "RELIANCE", "ITC", "HINDUNILVR", "TATAMOTORS",
    "MARUTI", "SUNPHARMA"
]

def render_dashboard(metrics, is_simulation=False):
    """Reusable layout to render KPI metrics, holdings table, and the AI Explainer"""
    
    # 1. KPI Badges
    col1, col2, col3, col4 = st.columns(4)
    label_pnl = "Hypothetical P&L" if is_simulation else "Unrealized P&L"
    col1.metric("Total Portfolio Value", f"₹{metrics['total_value']:,.2f}")
    col2.metric(label_pnl, f"₹{metrics['total_pnl']:,.2f}", f"{metrics['pnl_percentage']}%")
    col3.metric("Concentration (HHI)", f"{metrics['herfindahl_index']}", f"{metrics['volatility_flag']} RISK")
    col4.metric("Top Sector", f"{metrics['top_sector']}", f"{metrics['top_sector_pct']}% Exposure")

    st.divider()

    # 2. Holdings Table
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
        if not api_key:
            st.error("Configuration Error: GEMINI_API_KEY is not configured in Streamlit Cloud Secrets.")
        else:
            status_text = "Evaluating planned allocation thresholds and sector drift..." if is_simulation else "Evaluating portfolio risk drivers and concentration..."
            with st.spinner(status_text):
                client = genai.Client(api_key=api_key)
                
                context_instruction = (
                    "The user is planning a hypothetical trade allocation before investing."
                    if is_simulation else
                    "The user is analyzing their existing portfolio."
                )

                prompt = f"""
                You are the Zerodha Portfolio Intelligence Explainer.
                Context: {context_instruction}

                Analyze the following portfolio metrics:
                - Total Capital: ₹{metrics['total_value']}
                - Herfindahl Index (HHI): {metrics['herfindahl_index']} (Threshold: >2500 indicates high concentration risk)
                - Top Sector Exposure: {metrics['top_sector']} at {metrics['top_sector_pct']}% of portfolio
                - Dominant/Worst Driver: {metrics['worst_performer']}

                STRICT GUIDELINES:
                1. If this is a simulation, evaluate whether the planned capital allocation is well-balanced or excessively concentrated.
                2. Explicitly point out any sector bias or single-stock concentration risk based on the HHI score.
                3. DO NOT give direct buy, sell, or price-target recommendations.
                4. Highlight one educational 'Risk Alert' or 'Diversification Opportunity'.
                5. End strictly with:
                'Disclaimer: Automated, non-discretionary insight for educational and review purposes only.'
                """
                
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )
                
                st.info(response.text)


# --- Application Navigation Tabs ---
tab_holdings, tab_simulate = st.tabs(["📊 Existing Holdings / CSV", "🧪 What-If Simulation Sandbox"])

# ==========================================
# TAB 1: Existing Holdings / CSV Upload
# ==========================================
with tab_holdings:
    st.sidebar.header("📁 Upload Existing Portfolio")
    uploaded_file = st.sidebar.file_uploader(
        "Upload Broker CSV", 
        type=["csv"],
        help="Compatible with Zerodha Console holdings exports"
    )

    if uploaded_file is not None:
        data_source = uploaded_file
        st.sidebar.success(f"Loaded: {uploaded_file.name}")
    elif os.path.exists("data/sample_portfolio.csv"):
        data_source = "data/sample_portfolio.csv"
    elif os.path.exists("sample_portfolio.csv"):
        data_source = "sample_portfolio.csv"
    else:
        data_source = pd.DataFrame([
            {"symbol": "INFY", "quantity": 50, "avg_price": 1400.0, "current_price": 1350.0},
            {"symbol": "TCS", "quantity": 25, "avg_price": 3500.0, "current_price": 3420.0},
            {"symbol": "HDFCBANK", "quantity": 40, "avg_price": 1480.0, "current_price": 1530.0},
            {"symbol": "RELIANCE", "quantity": 30, "avg_price": 2400.0, "current_price": 2480.0},
            {"symbol": "ITC", "quantity": 100, "avg_price": 410.0, "current_price": 435.0}
        ])

    try:
        metrics = compute_portfolio_analytics(data_source)
        render_dashboard(metrics, is_simulation=False)
    except Exception as e:
        st.error(f"Error reading portfolio data: {e}")

# ==========================================
# TAB 2: Interactive Sandbox (What-If)
# ==========================================
with tab_simulate:
    st.markdown("### 🛠️ Pre-Trade Allocation Sandbox")
    st.write("Add stocks, adjust quantities, or change prices below to test risk exposure before executing trades.")

    # Default starting basket for testing
    initial_sandbox_data = pd.DataFrame([
        {"symbol": "RELIANCE", "quantity": 20, "avg_price": 2500.0, "current_price": 2500.0},
        {"symbol": "TCS", "quantity": 15, "avg_price": 3400.0, "current_price": 3400.0},
        {"symbol": "HDFCBANK", "quantity": 30, "avg_price": 1550.0, "current_price": 1550.0},
        {"symbol": "INFY", "quantity": 40, "avg_price": 1350.0, "current_price": 1350.0}
    ])

    # Interactive table editor
    edited_df = st.data_editor(
        initial_sandbox_data,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "symbol": st.column_config.SelectboxColumn(
                "Stock Symbol",
                help="Select or enter NSE ticker symbol",
                options=SAMPLE_TICKERS,
                required=True
            ),
            "quantity": st.column_config.NumberColumn(
                "Target Quantity",
                min_value=1,
                step=1,
                required=True
            ),
            "avg_price": st.column_config.NumberColumn(
                "Expected Buy Price (₹)",
                min_value=1.0,
                format="₹%.2f",
                required=True
            ),
            "current_price": st.column_config.NumberColumn(
                "Current Market Price (₹)",
                min_value=1.0,
                format="₹%.2f",
                required=True
            )
        }
    )

    if edited_df.empty or edited_df["quantity"].sum() == 0:
        st.warning("Please add at least one stock with a quantity greater than zero to simulate.")
    else:
        try:
            sim_metrics = compute_portfolio_analytics(edited_df)
            render_dashboard(sim_metrics, is_simulation=True)
        except Exception as e:
            st.error(f"Simulation calculation error: {e}")
