# Esoda — AI-Powered Sales Analytics for Small Businesses

## Overview

Esoda is a conversational sales analytics tool built for small grocery store owners. It allows a non-technical business owner to upload their sales data, ask questions in plain English, and receive immediate answers in the form of plain language summaries and relevant charts.

The core idea: most small businesses generate data every day but have no practical way to extract meaning from it. Esoda bridges that gap.

## Live Demo

## Live Demo

🔗 **[Try Esoda Live](https://esodaapp.streamlit.app)**

Upload any sales CSV or Excel file and get instant insights — no configuration required.

> Sample dataset included: `data/freshmart_sales_data.csv`

## Features

- **Automatic Dashboard** — KPI cards, revenue and profit trends, product and category performance generated instantly on upload
- **AI Question Mode** — ask any business question in plain English and get a written answer with observations and recommendations
- **Smart Column Mapping** — works with any POS export regardless of column names. AI auto-detects and maps columns automatically
- **Cascading Filters** — filter by date range, category and product. All KPIs, charts and insights update in real time
- **Insight Engine** — 12 independent rules that automatically surface observations like margin compression, hidden gem products, revenue concentration risk and sustained sales declines

## Tech Stack

| Layer | Tool |
|---|---|
| UI & Application | Streamlit |
| Data Processing | Pandas, NumPy |
| Visualisations | Plotly |
| AI Layer | Anthropic Claude API |
| Language | Python |

## Project Structure

```
esoda/
├── core/
│   ├── ingestion.py      # Data loading, cleaning and enrichment
│   ├── kpis.py           # KPI calculations and trend analysis
│   ├── insights.py       # Automated insight rules engine
│   └── ai_analyst.py     # Claude API integration
├── data/
│   └── freshmart_sales_data.csv
├── esoda.py              # Main Streamlit application
└── requirements.txt
```

## Running Locally

```bash
# Clone the repository
git clone https://github.com/GeorgeKakweza/esoda.git
cd esoda

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Add your Anthropic API key
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Run the app
streamlit run esoda.py
```

## Data Schema

Esoda accepts any CSV or Excel file. Required fields:

| Field | Description |
|---|---|
| Date | Transaction date |
| Product | Product name |
| Category | Product category |
| Quantity | Units sold |
| Unit Price | Selling price per unit |
| Cost Per Unit | Cost price per unit |

Column names do not need to match exactly — Esoda uses AI to detect and map them automatically.

## What I Learned

This project gave me end-to-end experience across the full data product lifecycle:

- Translating a real business problem into a data schema and analytics architecture
- Building a modular Python analytics engine with independent, testable components
- Designing an insight rules engine that generates plain language business observations
- Integrating a production LLM API for both question answering and intelligent column detection
- Building and deploying a web application with Streamlit
- Thinking about user experience for non-technical users

## Author

George Kakweza — Data Scientist  
[GitHub](https://github.com/GeorgeKakweza)