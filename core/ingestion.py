import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "date",
    "product",
    "product_category",
    "quantity",
    "unit_price",
    "cost_per_unit",
]

def _normalize_columns(df):
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df

def _validate_columns(df):
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df

def _clean_data(df):
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    for col in ["quantity", "unit_price", "cost_per_unit"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["quantity", "unit_price", "cost_per_unit"])
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0) & (df["cost_per_unit"] > 0)]
    for col in ["product", "product_category"]:
        df[col] = df[col].astype(str).str.strip()
    return df.reset_index(drop=True)

def _enrich_data(df):
    df["revenue"] = df["quantity"] * df["unit_price"]
    df["total_cost"] = df["quantity"] * df["cost_per_unit"]
    df["profit"] = df["revenue"] - df["total_cost"]
    df["profit_margin"] = (df["profit"] / df["revenue"]) * 100
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.strftime("%b")
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.dayofweek >= 5
    return df

def load_data(source):
    if isinstance(source, pd.DataFrame):
        df = source.copy()
    elif hasattr(source, 'name') and source.name.endswith('.xlsx'):
        df = pd.read_excel(source)
    else:
        df = pd.read_csv(source)
    
    df = _normalize_columns(df)
    df = _validate_columns(df)
    df = _clean_data(df)
    df = _enrich_data(df)
    return df

if __name__ == "__main__":
    df = load_data("data/freshmart_sales_data.csv")
    print(df.shape)
    print(df.columns.tolist())