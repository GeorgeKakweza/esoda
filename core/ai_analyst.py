import os
import anthropic
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def build_data_context(df):
    
    # Monthly product performance
    monthly_product = df.groupby(["year_month", "product"]).agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        units=("quantity", "sum")
    ).reset_index()
    
    # Last 3 months product performance
    last_3_months = sorted(df["year_month"].unique())[-3:]
    recent_products = monthly_product[
        monthly_product["year_month"].isin(last_3_months)
    ].sort_values(["year_month", "revenue"], ascending=[True, False])
    
    # Product level summary
    product_summary = df.groupby("product").agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
        units=("quantity", "sum"),
        margin=("profit_margin", "mean")
    ).round(2).sort_values("revenue", ascending=False)

    # Category monthly trend
    category_monthly = df.groupby(["year_month", "product_category"]).agg(
        revenue=("revenue", "sum"),
        profit=("profit", "sum"),
    ).reset_index().sort_values(["year_month", "revenue"], ascending=[True, False])

    context = f"""
    BUSINESS DATA CONTEXT FOR FRESHMART GROCERY STORE
    
    === OVERALL SUMMARY ===
    - Total transactions: {len(df):,}
    - Date range: {df['date'].min().date()} to {df['date'].max().date()}
    - Total revenue: ${df['revenue'].sum():,.2f}
    - Total profit: ${df['profit'].sum():,.2f}
    - Overall profit margin: {(df['profit'].sum() / df['revenue'].sum() * 100):.1f}%
    - Total units sold: {df['quantity'].sum():,}
    - Number of products: {df['product'].nunique()}
    - Categories: {', '.join(df['product_category'].unique())}

    === ALL PRODUCTS (Revenue, Profit, Units, Avg Margin) ===
    {product_summary.to_string()}

    === MONTHLY REVENUE & PROFIT TREND ===
    {df.groupby('year_month').agg(revenue=('revenue','sum'), profit=('profit','sum'), units=('quantity','sum')).to_string()}

    === RECENT 3 MONTHS PRODUCT PERFORMANCE ===
    {recent_products.to_string(index=False)}

    === CATEGORY MONTHLY PERFORMANCE ===
    {category_monthly.to_string(index=False)}

    === DAY OF WEEK PERFORMANCE ===
    {df.groupby('day_of_week').agg(revenue=('revenue','sum'), profit=('profit','sum'), units=('quantity','sum')).to_string()}
    """
    return context


def ask_question(df, question):
    context = build_data_context(df)
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a professional sales analyst helping a small grocery store owner understand their business data.

Here is the business data context:
{context}

The business owner asks: {question}

Please provide:
1. A clear, plain English answer to their question
2. 2-3 specific observations from the data
3. 1-2 actionable recommendations

Keep your response concise and avoid technical jargon. Write as if you are talking directly to a non-technical business owner."""
            }
        ]
    )
    
    return message.content[0].text


def detect_columns(df_raw):
    import json
    
    sample = df_raw.head(3).to_string()
    columns = df_raw.columns.tolist()
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": f"""You are a data analyst helping map CSV columns to a sales analytics schema.

The uploaded file has these columns:
{columns}

Here are the first 3 rows of data:
{sample}

Map the uploaded columns to these required fields:
- date: transaction date
- product: product name
- product_category: product category or department
- quantity: units sold
- unit_price: selling price per unit
- cost_per_unit: cost price per unit

Also identify these optional fields if present:
- transaction_id: unique transaction identifier
- product_id: unique product code
- product_subcategory: product subcategory

Respond ONLY with a valid JSON object. No explanation, no markdown, no backticks. Just the raw JSON:
{{
    "date": "column_name_or_null",
    "product": "column_name_or_null",
    "product_category": "column_name_or_null",
    "quantity": "column_name_or_null",
    "unit_price": "column_name_or_null",
    "cost_per_unit": "column_name_or_null",
    "transaction_id": "column_name_or_null",
    "product_id": "column_name_or_null",
    "product_subcategory": "column_name_or_null"
}}"""
            }
        ]
    )
    
    response_text = message.content[0].text.strip()
    
    # Clean up response in case Claude added markdown backticks
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    
    response_text = response_text.strip()
    
    try:
        mapping = json.loads(response_text)
    except json.JSONDecodeError:
        # Return empty mapping if parsing fails
        mapping = {field: None for field in [
            "date", "product", "product_category", "quantity", 
            "unit_price", "cost_per_unit", "transaction_id", 
            "product_id", "product_subcategory"
        ]}
    
    return mapping


if __name__ == "__main__":
    from ingestion import load_data
    
    df = load_data("data/freshmart_sales_data.csv")
    
    question = "which were the top 3 most profitable products in December of both years?"
    answer = ask_question(df, question)
    print(answer)