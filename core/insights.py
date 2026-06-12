import pandas as pd
import numpy as np

from core.kpis import (
    get_monthly_trend,
    get_product_performance,
    get_category_performance,
)


SEVERITY = {
    "positive": "positive",
    "warning": "warning",
    "negative": "negative",
    "neutral": "neutral",
}


def generate_insights(df, kpis):
    insights = []
    
    monthly = get_monthly_trend(df)
    products = get_product_performance(df)
    categories = get_category_performance(df)
    
    rules = [
        _revenue_trend,
        _margin_compression,
        _top3_concentration,
        _hidden_gem_product,
        _worst_margin_product,
        _sustained_decline,
        _weekend_vs_weekday,
        _low_margin_high_revenue,
    ]
    
    for rule in rules:
        try:
            result = rule(df, kpis, monthly, products, categories)
            if result:
                insights.append(result)
        except Exception:
            pass
    
    return insights


def _revenue_trend(df, kpis, monthly, products, categories):
    rev_change = kpis.get("mom_revenue_change_pct")
    if rev_change is None:
        return None
    
    latest = kpis.get("latest_month")
    previous = kpis.get("previous_month")
    
    if rev_change >= 10:
        return {
            "title": "Strong Revenue Growth",
            "observation": f"Revenue grew by {rev_change:.1f}% from {previous} to {latest}. This is a strong month on month improvement.",
            "severity": SEVERITY["positive"],
        }
    elif rev_change <= -10:
        return {
            "title": "Significant Revenue Decline",
            "observation": f"Revenue dropped by {abs(rev_change):.1f}% from {previous} to {latest}. This requires immediate attention.",
            "severity": SEVERITY["negative"],
        }
    elif rev_change <= -2:
        return {
            "title": "Revenue Softening",
            "observation": f"Revenue declined by {abs(rev_change):.1f}% from {previous} to {latest}. Monitor whether this continues.",
            "severity": SEVERITY["warning"],
        }
    return None


def _margin_compression(df, kpis, monthly, products, categories):
    if len(monthly) < 3:
        return None
    
    recent = monthly.tail(3)
    margin_trend = recent["profit_margin_pct"].values
    
    if margin_trend[-1] < margin_trend[-2] < margin_trend[-3]:
        drop = round(margin_trend[-3] - margin_trend[-1], 1)
        return {
            "title": "Margin Compression Detected",
            "observation": f"Profit margin has declined for 3 consecutive months, shrinking by {drop} percentage points. Costs may be growing faster than revenue.",
            "severity": SEVERITY["negative"],
        }
    return None


def _top3_concentration(df, kpis, monthly, products, categories):
    
    top3 = products.nlargest(3, "revenue")["product"].tolist()
    names = ", ".join(top3)
    total_revenue = products["revenue"].sum()
    top3_revenue = products.nlargest(3, "revenue")["revenue"].sum()
    concentration = round((top3_revenue / total_revenue) * 100, 2)

    if concentration >= 60:
        return {
            "title": "High Revenue Concentration Risk",
            "observation": f"Just 3 products — {names} — account for {concentration}% of total revenue. A disruption to any of these would significantly impact the business.",
            "severity": SEVERITY["warning"],
        }
    elif concentration >= 40:
        return {
            "title": "Moderate Revenue Concentration",
            "observation": f"The top 3 products ({names}) generate {concentration}% of total revenue. Worth monitoring.",
            "severity": SEVERITY["neutral"],
        }
    return None


def _hidden_gem_product(df, kpis, monthly, products, categories):
    median_revenue = products["revenue"].median()
    q75_margin = products["profit_margin_pct"].quantile(0.75)

    gems = products[
        (products["profit_margin_pct"] >= q75_margin) &
        (products["revenue"] < median_revenue)
    ]

    if gems.empty:
        return None

    gem = gems.sort_values("profit_margin_pct", ascending=False).iloc[0]
    return {
        "title": "Hidden Gem Product Identified",
        "observation": f"{gem['product']} has a profit margin of {gem['profit_margin_pct']:.1f}% but generates below average revenue. Increasing its visibility could improve overall profitability.",
        "severity": SEVERITY["positive"],
    }


def _worst_margin_product(df, kpis, monthly, products, categories):
    high_rev = products[products["revenue"] >= products["revenue"].quantile(0.75)]
    
    if high_rev.empty:
        return None

    worst = high_rev.sort_values("profit_margin_pct").iloc[0]
    
    if worst["profit_margin_pct"] < 15:
        return {
            "title": "High Revenue, Low Margin Warning",
            "observation": f"{worst['product']} is a top revenue contributor but has only a {worst['profit_margin_pct']:.1f}% profit margin. It may be driving sales volumes while contributing little to actual profitability.",
            "severity": SEVERITY["warning"],
        }
    return None


def _sustained_decline(df, kpis, monthly, products, categories):
    if len(monthly) < 4:
        return None

    recent_months = monthly.tail(4)["year_month"].tolist()
    
    product_monthly = df.groupby(["year_month", "product"])["revenue"].sum().reset_index()
    
    declining = []
    for product_name in product_monthly["product"].unique():
        pdata = product_monthly[
            (product_monthly["product"] == product_name) &
            (product_monthly["year_month"].isin(recent_months))
        ].sort_values("year_month")

        if len(pdata) < 4:
            continue

        revenues = pdata["revenue"].values
        if revenues[-1] < revenues[-2] < revenues[-3] < revenues[-4]:
            declining.append(product_name)

    if declining:
        names = ", ".join(declining[:3])
        suffix = f" and {len(declining) - 3} more" if len(declining) > 3 else ""
        return {
            "title": "Sustained Sales Decline Detected",
            "observation": f"{names}{suffix} has seen declining revenue for 4 consecutive months. Review pricing, shelf placement, or whether demand is shifting.",
            "severity": SEVERITY["negative"],
        }
    return None


def _weekend_vs_weekday(df, kpis, monthly, products, categories):
    weekend_daily = df[df["is_weekend"]].groupby("date")["revenue"].sum().mean()
    weekday_daily = df[~df["is_weekend"]].groupby("date")["revenue"].sum().mean()

    if weekday_daily == 0:
        return None

    uplift = round(((weekend_daily - weekday_daily) / weekday_daily) * 100, 2)

    if uplift >= 20:
        return {
            "title": "Weekends Drive Significantly Higher Sales",
            "observation": f"Weekend daily revenue is {uplift}% higher than weekday daily revenue. Consider increasing staff and stock levels on weekends to maximise this opportunity.",
            "severity": SEVERITY["neutral"],
        }
    elif uplift <= -20:
        return {
            "title": "Weekdays Outperform Weekends",
            "observation": f"Weekday daily revenue is {abs(uplift)}% higher than weekends. Your peak trading days are Monday to Friday.",
            "severity": SEVERITY["neutral"],
        }
    return None


def _low_margin_high_revenue(df, kpis, monthly, products, categories):
    high_rev_cats = categories[categories["revenue_share_pct"] >= 15]
    
    if high_rev_cats.empty:
        return None

    low_margin = high_rev_cats[high_rev_cats["profit_margin_pct"] < 20]
    
    if low_margin.empty:
        return None

    cat = low_margin.sort_values("profit_margin_pct").iloc[0]
    return {
        "title": f"{cat['product_category']}: High Revenue, Thin Margin",
        "observation": f"The {cat['product_category']} category generates {cat['revenue_share_pct']:.1f}% of revenue but operates on only a {cat['profit_margin_pct']:.1f}% margin. Consider reviewing pricing or supplier costs in this category.",
        "severity": SEVERITY["warning"],
    }


if __name__ == "__main__":
    from core.ingestion import load_data
    from core.kpis import calculate_kpis

    df = load_data("data/freshmart_sales_data.csv")
    kpis = calculate_kpis(df)
    
    insights = generate_insights(df, kpis)
    
    print(f"=== {len(insights)} INSIGHTS GENERATED ===\n")
    for insight in insights:
        print(f"[{insight['severity'].upper()}] {insight['title']}")
        print(f"{insight['observation']}")
        print()