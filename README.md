# RCECOS — Risk Committee Expertise & Credit Risk Oversight System
**HIT400 Research Project | Tadiwa Chokuona (H220460J)**
*Department of Forensic Accounting & Auditing*

## Overview
A Streamlit decision-support dashboard for assessing risk committee financial expertise and monitoring credit risk indicators in Zimbabwean commercial banks.

## Features
- **Overview** — Sector-wide NPL trends, expertise vs NPL scatter, bank snapshot table
- **Committee Expertise** — Member profiles, expertise scoring, governance registry, expertise–NPL regression
- **Credit Risk Indicators** — NPL bars, sector exposure radar, provisioning vs overdue, LDR heatmap, manual data entry
- **Early Warning** — Configurable thresholds, automated alert flags, NPL trajectory with risk zones
- **Reporting** — Board-ready governance reports, recommendations, CSV export

## Installation & Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens at http://localhost:8501

## Data
The app uses synthetic but realistic sample data for 7 Zimbabwean banks (2018–2024).
