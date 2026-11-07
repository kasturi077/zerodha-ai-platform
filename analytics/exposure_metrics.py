import numpy as np
import pandas as pd

# Built-in sector lookup for common Indian equities
SECTOR_MAP = {
    "INFY": "Information Technology",
    "TCS": "Information Technology",
    "WIPRO": "Information Technology",
    "HCLTECH": "Information Technology",
    "HDFCBANK": "Banking & Financials",
    "ICICIBANK": "Banking & Financials",
    "SBIN": "Banking & Financials",
    "KOTAKBANK": "Banking & Financials",
    "RELIANCE": "Energy & Conglomerate",
    "ITC": "Consumer Goods (FMCG)",
    "HINDUNILVR": "Consumer Goods (FMCG)",
    "TATAMOTORS": "Automobile",
    "MARUTI": "Automobile",
    "SUNPHARMA": "Healthcare & Pharma"
}

def clean_and_normalize_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Lowercase, strip whitespace, and remove dots/symbols from column headers
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r'[._]', ' ', regex=True)
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()
    )

    # 2. Match cleaned strings
    column_aliases = {
        'instrument': 'symbol',
        'tradingsymbol': 'symbol',
        'ticker': 'symbol',
        'qty': 'quantity',
        'avg cost': 'avg_price',
        'buy avg': 'avg_price',
        'buy price': 'avg_price',
        'average price': 'avg_price',
        'ltp': 'current_price',
        'last price': 'current_price',
        'market price': 'current_price'
    }
    df = df.rename(columns=column_aliases)

# 2. Rename known broker variations (Zerodha, Groww, AngelOne, Upstox)
    column_aliases = {
        'instrument': 'symbol',
        'tradingsymbol': 'symbol',
        'ticker': 'symbol',
        'stock': 'symbol',
        'qty': 'quantity',
        'qty.': 'quantity',
        'quantity': 'quantity',
        'available qty': 'quantity',
        'avg. cost': 'avg_price',
        'avg cost': 'avg_price',
        'buy avg': 'avg_price',
        'buy avg.': 'avg_price',
        'buy_price': 'avg_price',
        'average price': 'avg_price',
        'ltp': 'current_price',
        'last price': 'current_price',
        'market price': 'current_price',
        'cur. val': 'current_value',
        'cur. value': 'current_value'
    }
    df = df.rename(columns=column_aliases)

    # 3. Check for the absolute essential trio: symbol, quantity, avg_price
    essential_cols = {'symbol', 'quantity', 'avg_price'}
    if not essential_cols.issubset(df.columns):
        missing = essential_cols - set(df.columns)
        raise ValueError(
            f"CSV is missing basic position data: {', '.join(missing)}. "
            "Please upload a holdings export from Zerodha Console or your broker."
        )

    # 4. If current_price is missing, fallback to avg_price (0% baseline P&L)
    if 'current_price' not in df.columns:
        df['current_price'] = df['avg_price']

    # 5. Clean symbols (e.g., remove NSE: prefix if present)
    df['symbol'] = df['symbol'].astype(str).str.replace('NSE:', '').str.replace('BSE:', '').str.strip().str.upper()

    # 6. Auto-assign sector if missing or empty
    if 'sector' not in df.columns:
        df['sector'] = df['symbol'].map(SECTOR_MAP).fillna("Diversified / Other")
    else:
        df['sector'] = df['sector'].fillna("Diversified / Other")

    return df

def compute_portfolio_analytics(source="data/sample_portfolio.csv"):
    if isinstance(source, pd.DataFrame):
        df = source.copy()
    else:
        df = pd.read_csv(source)
    
    # Run the normalizer
    df = clean_and_normalize_portfolio(df)

    # Calculations
    df['current_val'] = df['quantity'] * df['current_price']
    df['cost_basis'] = df['quantity'] * df['avg_price']
    df['pnl'] = df['current_val'] - df['cost_basis']
    
    total_val = df['current_val'].sum()
    total_cost = df['cost_basis'].sum()
    total_pnl = df['pnl'].sum()
    portfolio_pnl_pct = (total_pnl / total_cost) * 100 if total_cost != 0 else 0.0
    
    df['weight'] = df['current_val'] / total_val if total_val != 0 else 0.0
    hhi = np.sum((df['weight'] * 100) ** 2)
    
    sector_sums = df.groupby('sector')['weight'].sum()
    top_sector_name = sector_sums.idxmax() if not sector_sums.empty else "N/A"
    top_sector_pct = (sector_sums.max() * 100) if not sector_sums.empty else 0.0
    
    worst_performer = df.sort_values(by='pnl').iloc[0]['symbol'] if not df.empty else "N/A"

    return {
        "df": df,
        "total_value": round(float(total_val), 2),
        "total_pnl": round(float(total_pnl), 2),
        "pnl_percentage": round(float(portfolio_pnl_pct), 2),
        "herfindahl_index": round(float(hhi), 2),
        "top_sector": top_sector_name,
        "top_sector_pct": round(float(top_sector_pct), 2),
        "worst_performer": worst_performer,
        "volatility_flag": "ELEVATED" if hhi > 2500 else "BALANCED"
    }
