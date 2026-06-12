import pandas as pd
import numpy as np

def calculate_kpis(df):
    total_revenue = df["revenue"].sum()
    total_cost = df["total_cost"].sum()
    total_profit = df["profit"].sum()
    total_units = int(df["quantity"].sum())
    total_transactions = len(df)
    avg_transaction_value = df["revenue"].mean()
    avg_daily_revenue = df.groupby("date")["revenue"].sum().mean()
    overall_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0

    period = get_period_comparison(df)

    result = {
        "total_revenue": round(total_revenue, 2),
        "total_cost": round(total_cost, 2),
        "total_profit": round(total_profit, 2),
        "overall_margin_pct": round(overall_margin, 2),
        "total_units_sold": total_units,
        "total_transactions": total_transactions,
        "avg_transaction_value": round(avg_transaction_value, 2),
        "avg_daily_revenue": round(avg_daily_revenue, 2),
    }

    if period:
        result.update(period)

    return result

def get_monthly_trend(df):
    monthly = df.groupby("year_month").agg(
        revenue=("revenue", "sum"),
        total_cost=("total_cost", "sum"),
        profit=("profit", "sum"),
        units=("quantity", "sum"),
        transactions=("revenue", "count"),
    ).reset_index()
    monthly["profit_margin_pct"] = (monthly["profit"] / monthly["revenue"] * 100).round(2)
    return monthly.sort_values("year_month")


def get_product_performance(df):
    product = df.groupby(["product_id", "product", "product_category"]).agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        units=("quantity", "sum"),
        transactions=("revenue", "count"),
    ).reset_index()
    product["profit_margin_pct"] = (product["profit"] / product["revenue"] * 100).round(2)
    product["revenue_share_pct"] = (product["revenue"] / product["revenue"].sum() * 100).round(2)
    product["profit_share_pct"] = (product["profit"] / product["profit"].sum() * 100).round(2)
    return product.sort_values("revenue", ascending=False)

def get_category_performance(df):
    category = df.groupby("product_category").agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        total_cost=("total_cost", "sum"),
        units=("quantity", "sum"),
        transactions=("revenue", "count"),
    ).reset_index()
    category["profit_margin_pct"] = (category["profit"] / category["revenue"] * 100).round(2)
    category["revenue_share_pct"] = (category["revenue"] / category["revenue"].sum() * 100).round(2)
    category["profit_share_pct"] = (category["profit"] / category["profit"].sum() * 100).round(2)
    return category.sort_values("revenue", ascending=False)


def get_period_comparison(df):
    monthly = get_monthly_trend(df)
    
    if len(monthly) < 2:
        return None
    
    latest = monthly.iloc[-1]
    previous = monthly.iloc[-2]
    
    def pct_change(new, old):
        if old == 0:
            return None
        return round(((new - old) / old) * 100, 2)
    
    return {
        "latest_month": latest["year_month"],
        "previous_month": previous["year_month"],
        "latest_revenue": round(latest["revenue"], 2),
        "previous_revenue": round(previous["revenue"], 2),
        "mom_revenue_change_pct": pct_change(latest["revenue"], previous["revenue"]),
        "latest_profit": round(latest["profit"], 2),
        "previous_profit": round(previous["profit"], 2),
        "mom_profit_change_pct": pct_change(latest["profit"], previous["profit"]),
        "latest_units": int(latest["units"]),
        "previous_units": int(previous["units"]),
        "mom_units_change_pct": pct_change(latest["units"], previous["units"]),
    }


def get_day_of_week_performance(df):
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day = df.groupby("day_of_week").agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        units=("quantity", "sum"),
        transactions=("revenue", "count"),
    ).reset_index()
    day["avg_revenue"] = (day["revenue"] / day["transactions"]).round(2)
    day["day_of_week"] = pd.Categorical(day["day_of_week"], categories=days_order, ordered=True)
    return day.sort_values("day_of_week")


if __name__ == "__main__":
    from ingestion import load_data
    
    df = load_data("data/freshmart_sales_data.csv")
    
    kpis = calculate_kpis(df)
    print("=== KPIs ===")
    for k, v in kpis.items():
        print(f"  {k}: {v}")
    
    print("\n=== MONTHLY TREND (last 3 months) ===")
    monthly = get_monthly_trend(df)
    print(monthly.tail(3).to_string(index=False))
    
    print("\n=== TOP 5 PRODUCTS ===")
    products = get_product_performance(df)
    print(products[["product", "revenue", "profit", "profit_margin_pct"]].head(5).to_string(index=False))
    
    print("\n=== CATEGORY PERFORMANCE ===")
    categories = get_category_performance(df)
    print(categories.to_string(index=False))