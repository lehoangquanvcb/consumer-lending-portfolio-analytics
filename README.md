# Consumer Lending Portfolio Analytics Workbench V2

An end-to-end portfolio analytics platform for consumer lending, built with **Excel, Python, GitHub and Streamlit**.

## Modules
1. Executive Overview
2. Portfolio Overview
3. Vintage Analysis
4. Roll Rate Analysis
5. DPD Migration
6. Delinquency Analysis
7. Collection Analytics
8. Portfolio Profitability
9. Early Warning
10. Risk Indicators
11. MIS Dashboard
12. Management Report
13. Data Dictionary

## Project Structure
```text
consumer_lending_portfolio_analytics_workbench_v1/
├── app.py
├── requirements.txt
├── README.md
├── modules/
│   ├── __init__.py
│   └── data_engine.py
└── data/
    ├── Consumer_Lending_Portfolio_Data_Model.xlsx
    ├── loan_master.csv
    ├── monthly_snapshots.csv
    └── assumptions.csv
```

## Run Locally
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

For macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Upload to GitHub
```bash
git init
git add .
git commit -m "Initial Consumer Lending Portfolio Analytics Workbench"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/consumer-lending-portfolio-analytics.git
git push -u origin main
```

## Deploy on Streamlit Community Cloud
1. Push the project to a public GitHub repository.
2. Open Streamlit Community Cloud.
3. Select **New app**.
4. Choose the repository, `main` branch and `app.py`.
5. Click **Deploy**.

## Replacing Synthetic Data
Replace files in `/data` while preserving the field names shown in `Data_Dictionary` and the Excel workbook.

## Important
The dataset is synthetic and for demonstration only. It does not represent any real customer or financial institution.


## V2 Interface Upgrade
V2 replaces the standard tab-based layout with:
- Fixed left sidebar navigation
- Horizontal top filter bar
- Six visual KPI cards with prior-month movement
- Three-row executive dashboard grid
- Dark enterprise dashboard theme
- Dedicated detailed pages for every analytical module

The analytical engine and synthetic source data are inherited from V1.


## V3 – Fincon JD Fit
Adds Credit Policy Simulator, Champion–Challenger, Vintage Diagnostic, NPL Stock–Flow, Advanced Collection, Risk Appetite, Stress Testing, Action Tracker, Data Quality controls and SQL reference scripts.


## V4 – Portfolio Strategy & Advisory Platform

V4 consolidates the long V3 menu into 12 decision-oriented workspaces and removes duplicate standalone pages from navigation.

New V4 layer:
- Portfolio Decision Cockpit
- Forward-Looking Forecast
- Strategy Optimizer
- Consolidated Strategy Lab
- Risk-Based Pricing
- Collection Strategy Simulator
- Management Insight & Advisory Engine
- Synthetic Partner Benchmarking
- Management Pack Generator
- Consolidated Data & Governance

Core workflow:
Portfolio Performance → Risk Diagnosis → Forecast → Strategy Simulation → Management Recommendation → Decision → Action Tracking → Reporting

All market/peer benchmark values included in the demonstration are synthetic.


## V4 Fixed 2
- Updated visible application title to include Author: Le Hoang Quan.
- Rebuilt Portfolio Overview as a stable responsive 2x2 chart layout.
- Fixed NameError caused by undefined c3/c4 columns.
