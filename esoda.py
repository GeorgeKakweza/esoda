from core.ai_analyst import ask_question, detect_columns
import streamlit as st
import pandas as pd
from core.ingestion import load_data
from core.kpis import (
    calculate_kpis,
    get_monthly_trend,
    get_product_performance,
    get_category_performance,
    get_period_comparison,
    get_day_of_week_performance,
)
from core.insights import generate_insights

st.set_page_config(
    page_title="Esoda",
    page_icon="📊",
    layout="wide",
)


st.title("📊 Esoda")
st.caption("Your personal sales analyst")

st.divider()

uploaded_file = st.file_uploader(
    "Upload your sales file to get started",
    type=["csv", "xlsx"],
)


if uploaded_file is None:
    st.info("Please upload a CSV or Excel file to get started.")
    st.stop()


try:
    # Read raw file first without processing
    uploaded_file.seek(0)
    if uploaded_file.name.endswith(".csv"):
        df_raw = pd.read_csv(uploaded_file)
    else:
        df_raw = pd.read_excel(uploaded_file)
    
    df_raw.columns = [c.strip().lower().replace(" ", "_") for c in df_raw.columns]
    
    REQUIRED = ["date", "product", "product_category", "quantity", "unit_price", "cost_per_unit"]
    missing = [col for col in REQUIRED if col not in df_raw.columns]
    
    if missing:
        st.warning("Your column names don't match our expected format. Let me detect them automatically...")
        
        with st.spinner("Detecting column mapping..."):
            mapping = detect_columns(df_raw)
        
        st.subheader("Column Mapping")
        st.write("Please confirm or adjust the detected column mapping:")
        
        confirmed_mapping = {}
        cols = st.columns(2)
        
        required_fields = {
            "date": "Date",
            "product": "Product Name",
            "product_category": "Product Category",
            "quantity": "Quantity Sold",
            "unit_price": "Unit Price",
            "cost_per_unit": "Cost Per Unit",
        }
        
        for i, (field, label) in enumerate(required_fields.items()):
            with cols[i % 2]:
                suggested = mapping.get(field)
                options = [None] + df_raw.columns.tolist()
                default_idx = options.index(suggested) if suggested in options else 0
                confirmed_mapping[field] = st.selectbox(
                    f"{label}",
                    options=options,
                    index=default_idx,
                    key=f"map_{field}"
                )
        
        if st.button("Confirm Mapping and Analyse"):
            rename_dict = {v: k for k, v in confirmed_mapping.items() if v is not None}
            df_raw = df_raw.rename(columns=rename_dict)
            uploaded_file.seek(0)
            df = load_data(df_raw)
            st.success(f"File loaded successfully. {len(df):,} transactions loaded.")
        else:
            st.stop()
    else:
        df = load_data(df_raw)
        st.success(f"File uploaded successfully. {len(df):,} transactions loaded.")

except ValueError as e:
    st.error(f"There was a problem with your file: {e}")
    st.stop()

#-----------------------------------------------------------

kpis = calculate_kpis(df)

st.subheader("Business Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Revenue", f"${kpis['total_revenue']:,.2f}")

with col2:
    st.metric("Total Profit", f"${kpis['total_profit']:,.2f}")

with col3:
    st.metric("Profit Margin", f"{kpis['overall_margin_pct']}%")

with col4:
    st.metric("Units Sold", f"{kpis['total_units_sold']:,}")


#-----------------------------------------------------------

col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric(
        "Revenue This Month",
        f"${kpis['latest_revenue']:,.2f}",
        delta=f"{kpis['mom_revenue_change_pct']}% vs last month"
    )

with col6:
    st.metric(
        "Profit This Month",
        f"${kpis['latest_profit']:,.2f}",
        delta=f"{kpis['mom_profit_change_pct']}% vs last month"
    )

with col7:
    st.metric(
        "Units This Month",
        f"{kpis['latest_units']:,}",
        delta=f"{kpis['mom_units_change_pct']}% vs last month"
    )

with col8:
    st.metric("Avg Daily Revenue", f"${kpis['avg_daily_revenue']:,.2f}")


#-----------------------------------------------------------

st.divider()
st.subheader("Revenue & Profit Trends")

import plotly.express as px

monthly = get_monthly_trend(df)

fig = px.line(
    monthly,
    x="year_month",
    y=["revenue", "profit"],
    labels={"year_month": "Month", "value": "Amount ($)", "variable": "Metric"},
    title="Monthly Revenue & Profit",
)
st.plotly_chart(fig, use_container_width=True)


#-----------------------------------------------------------

st.divider()
st.subheader("Product Performance")

products = get_product_performance(df)

col_left, col_right = st.columns(2)

with col_left:
    top10 = products.head(10)
    fig2 = px.bar(
        top10,
        x="revenue",
        y="product",
        orientation="h",
        title="Top 10 Products by Revenue",
        labels={"revenue": "Revenue ($)", "product": "Product"},
        color="profit_margin_pct",
        color_continuous_scale="Blues",
    )
    fig2.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig2, use_container_width=True)

with col_right:
    top10_profit = products.sort_values("profit", ascending=False).head(10)
    fig3 = px.bar(
        top10_profit,
        x="profit",
        y="product",
        orientation="h",
        title="Top 10 Products by Profit",
        labels={"profit": "Profit ($)", "product": "Product"},
        color="profit_margin_pct",
        color_continuous_scale="Greens",
    )
    fig3.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig3, use_container_width=True)

#-----------------------------------------------------------

st.divider()
st.subheader("Category Performance")

categories = get_category_performance(df)

fig4 = px.bar(
    categories,
    x="product_category",
    y=["revenue", "profit"],
    title="Revenue & Profit by Category",
    labels={"product_category": "Category", "value": "Amount ($)", "variable": "Metric"},
    barmode="group",
)
st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.subheader("💡 Key Insights")

insights = generate_insights(df, kpis)

if not insights:
    st.info("No significant insights detected for this dataset.")
else:
    for insight in insights:
        if insight["severity"] == "positive":
            st.success(f"**{insight['title']}** — {insight['observation']}")
        elif insight["severity"] == "negative":
            st.error(f"**{insight['title']}** — {insight['observation']}")
        elif insight["severity"] == "warning":
            st.warning(f"**{insight['title']}** — {insight['observation']}")
        else:
            st.info(f"**{insight['title']}** — {insight['observation']}")


#-----------------------------------------------------------chatbot
st.divider()
st.subheader("🤖 Ask Esoda")
st.caption("Ask any question about your sales data in plain English")

question = st.text_input(
    "Your question",
    placeholder="e.g. What were my best selling products last month?",
)

if question:
    with st.spinner("Analysing your data..."):
        answer = ask_question(df, question)
    st.markdown(answer)