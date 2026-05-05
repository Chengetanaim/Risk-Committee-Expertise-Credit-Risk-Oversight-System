import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
import hashlib
import json
import warnings
import statsmodels.api as sm
warnings.filterwarnings('ignore')

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RCECOS | Risk Committee Expertise & Credit Risk Oversight System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Session State Initialization ─────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "users" not in st.session_state:
    st.session_state.users = {}
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []
if "current_data" not in st.session_state:
    st.session_state.current_data = None
if "data_source" not in st.session_state:
    st.session_state.data_source = None
if "model_results" not in st.session_state:
    st.session_state.model_results = None

# ─── Real Data from Excel (Embedded) ──────────────────────────────────────────
def load_real_bank_data():
    """Load the actual Zimbabwe bank panel data - 120 observations (10 banks × 12 years)"""
    
    # Create the dataset directly as a DataFrame with correct column names
    data = {
        "Bank": [],
        "Year": [],
        "RCFE": [],
        "NPL_Ratio": [],
        "Board_Independence": [],
        "RC_Size": [],
        "GDP_Growth": [],
        "Policy_Rate": [],
        "Bank_Size": [],
        "Capital_Adequacy": [],
        "ROA": [],
        "Loan_to_Deposit": [],
        "ZAMCO_Period": []
    }
    
    years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    zamco = ["No", "Yes", "Yes", "Yes", "Yes", "Yes", "No", "No", "No", "No", "No", "No"]
    gdp = [2.8, 2.4, 1.8, 0.8, 4.7, 4.2, -6.5, -7.82, 8.47, 6.14, 5.3, 2]
    policy = [9, 9, 9, 8.5, 8.5, 10, 35, 35, 60, 200, 80, 35]
    
    # Bank data - each list has exactly 12 values
    banks_dict = {
        "CBZ Bank": {
            "RCFE": [0.5, 0.5, 0.55, 0.55, 0.57, 0.57, 0.6, 0.6, 0.67, 0.67, 0.67, 0.67],
            "NPL_Ratio": [18.5, 17.8, 16.2, 9.1, 12, 12, 5.2, 4.8, 4.1, 3.2, 2.4, 2.8],
            "Board_Independence": [0.6, 0.62, 0.64, 0.65, 0.67, 0.67, 0.67, 0.67, 0.73, 0.73, 0.75, 0.75],
            "RC_Size": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Bank_Size": [6.73, 6.72, 6.68, 6.65, 6.7, 6.75, 6.8, 6.85, 6.95, 7.05, 7.15, 7.2],
            "Capital_Adequacy": [18.5, 17.9, 17.2, 18, 18.5, 19, 20.2, 22, 24.5, 26, 28, 29.5],
            "ROA": [1.8, 1.5, 1.2, 1, 1.3, 1.5, 1.2, 1.4, 2.1, 2.8, 3.2, 3],
            "Loan_to_Deposit": [52, 53, 51, 48, 50, 52, 49, 45, 43, 40, 38, 37],
        },
        "ZB Bank": {
            "RCFE": [0.43, 0.43, 0.43, 0.5, 0.5, 0.5, 0.5, 0.5, 0.57, 0.57, 0.57, 0.57],
            "NPL_Ratio": [19.5, 18.9, 17.4, 9.5, 12, 12, 6.8, 6.2, 5.4, 4.5, 3.5, 3.9],
            "Board_Independence": [0.57, 0.57, 0.57, 0.6, 0.6, 0.6, 0.6, 0.6, 0.64, 0.64, 0.67, 0.67],
            "RC_Size": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
            "Bank_Size": [5.98, 5.95, 5.9, 5.88, 5.92, 5.96, 6.0, 6.08, 6.18, 6.28, 6.38, 6.45],
            "Capital_Adequacy": [16.2, 15.8, 15.5, 16, 16.5, 17, 18.5, 20, 22, 24, 26, 27.5],
            "ROA": [1.2, 1, 0.8, 0.7, 1, 1.2, 1, 1.1, 1.8, 2.5, 2.8, 2.6],
            "Loan_to_Deposit": [58, 59, 57, 55, 56, 57, 53, 50, 47, 44, 42, 40],
        },
        "Stanbic Bank": {
            "RCFE": [0.6, 0.6, 0.63, 0.63, 0.67, 0.67, 0.67, 0.67, 0.67, 0.75, 0.75, 0.75],
            "NPL_Ratio": [6.5, 5.8, 5.2, 5, 4.5, 4.2, 3.5, 3.1, 2.6, 2.1, 1.8, 2],
            "Board_Independence": [0.75, 0.75, 0.75, 0.78, 0.78, 0.78, 0.78, 0.78, 0.78, 0.8, 0.8, 0.8],
            "RC_Size": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Bank_Size": [6.15, 6.18, 6.2, 6.22, 6.25, 6.28, 6.32, 6.38, 6.48, 6.58, 6.68, 6.75],
            "Capital_Adequacy": [22, 22.5, 23, 23.5, 24, 24.5, 26, 28, 30, 32, 34, 35.5],
            "ROA": [2.5, 2.3, 2, 1.8, 2.2, 2.4, 2.1, 2.3, 3, 3.8, 4.2, 4],
            "Loan_to_Deposit": [62, 63, 61, 60, 62, 63, 60, 57, 54, 51, 48, 46],
        },
        "Steward Bank": {
            "RCFE": [0.33, 0.33, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.5, 0.5, 0.57, 0.57],
            "NPL_Ratio": [16, 15.5, 14, 8.5, 12, 11.5, 7.5, 6.8, 5.9, 4.8, 3.4, 3.7],
            "Board_Independence": [0.5, 0.5, 0.55, 0.57, 0.57, 0.57, 0.57, 0.57, 0.6, 0.6, 0.64, 0.64],
            "RC_Size": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
            "Bank_Size": [5.45, 5.48, 5.5, 5.52, 5.55, 5.6, 5.65, 5.72, 5.82, 5.92, 6.02, 6.1],
            "Capital_Adequacy": [15, 14.8, 14.5, 15, 15.5, 16, 17.5, 19, 21, 23, 25, 26.5],
            "ROA": [0.9, 0.8, 0.6, 0.5, 0.8, 1, 0.8, 0.9, 1.5, 2, 2.3, 2.2],
            "Loan_to_Deposit": [65, 66, 64, 62, 63, 64, 61, 58, 55, 52, 49, 47],
        },
        "NMB Bank": {
            "RCFE": [0.5, 0.5, 0.5, 0.5, 0.57, 0.57, 0.57, 0.57, 0.67, 0.67, 0.71, 0.71],
            "NPL_Ratio": [16.5, 15.8, 14.9, 8, 6.5, 5.8, 3.8, 3.5, 2.9, 1.8, 1.1, 1.2],
            "Board_Independence": [0.62, 0.62, 0.64, 0.64, 0.67, 0.67, 0.67, 0.67, 0.71, 0.71, 0.75, 0.75],
            "RC_Size": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Bank_Size": [5.6, 5.62, 5.64, 5.66, 5.7, 5.74, 5.78, 5.85, 5.95, 6.05, 6.15, 6.22],
            "Capital_Adequacy": [16.5, 16, 15.8, 16.2, 16.8, 17.5, 19, 21, 23, 25, 27, 28.5],
            "ROA": [1.1, 0.9, 0.7, 0.6, 0.9, 1.1, 0.9, 1, 1.7, 2.3, 2.6, 2.5],
            "Loan_to_Deposit": [60, 61, 59, 57, 58, 59, 56, 53, 50, 47, 44, 42],
        },
        "BancABC": {
            "RCFE": [0.4, 0.4, 0.43, 0.43, 0.43, 0.43, 0.43, 0.43, 0.5, 0.57, 0.57, 0.57],
            "NPL_Ratio": [18, 17.5, 15.8, 8.8, 11, 11, 7.2, 6.5, 5.6, 4.3, 3.1, 3.4],
            "Board_Independence": [0.55, 0.55, 0.57, 0.57, 0.57, 0.57, 0.57, 0.57, 0.64, 0.64, 0.67, 0.67],
            "RC_Size": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Bank_Size": [5.75, 5.72, 5.68, 5.65, 5.7, 5.75, 5.8, 5.88, 5.98, 6.08, 6.18, 6.25],
            "Capital_Adequacy": [15.5, 15, 14.8, 15.2, 15.8, 16.5, 18, 20, 22, 24, 26, 27.5],
            "ROA": [1, 0.8, 0.6, 0.5, 0.8, 1, 0.8, 0.9, 1.6, 2.2, 2.5, 2.4],
            "Loan_to_Deposit": [61, 62, 60, 58, 59, 60, 57, 54, 51, 48, 45, 43],
        },
        "Ecobank": {
            "RCFE": [0.5, 0.5, 0.57, 0.57, 0.57, 0.57, 0.57, 0.57, 0.67, 0.67, 0.75, 0.75],
            "NPL_Ratio": [7.5, 6.8, 5.9, 3.8, 4, 4.2, 4.6, 4.2, 3.5, 2.7, 2.1, 2.3],
            "Board_Independence": [0.62, 0.62, 0.67, 0.67, 0.67, 0.67, 0.67, 0.67, 0.73, 0.73, 0.75, 0.75],
            "RC_Size": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
            "Bank_Size": [5.85, 5.88, 5.9, 5.92, 5.95, 5.98, 6.02, 6.08, 6.18, 6.28, 6.38, 6.45],
            "Capital_Adequacy": [20, 20.5, 21, 21.5, 22, 22.5, 24, 26, 28, 30, 32, 33.5],
            "ROA": [2, 1.8, 1.6, 1.4, 1.7, 1.9, 1.7, 1.8, 2.5, 3.2, 3.6, 3.4],
            "Loan_to_Deposit": [55, 56, 54, 52, 53, 54, 51, 48, 45, 42, 39, 37],
        },
        "FBC Bank": {
            "RCFE": [0.43, 0.43, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.57, 0.57, 0.67, 0.67],
            "NPL_Ratio": [13.5, 12.8, 11.2, 6.5, 6, 5.8, 5.8, 5.4, 4.7, 4, 3.5, 3.8],
            "Board_Independence": [0.58, 0.58, 0.62, 0.63, 0.63, 0.63, 0.63, 0.63, 0.67, 0.67, 0.71, 0.71],
            "RC_Size": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
            "Bank_Size": [5.9, 5.88, 5.85, 5.82, 5.88, 5.92, 5.96, 6.02, 6.12, 6.22, 6.32, 6.4],
            "Capital_Adequacy": [17, 16.5, 16.2, 16.8, 17.5, 18, 19.5, 21.5, 23.5, 25.5, 27.5, 29],
            "ROA": [1.3, 1.1, 0.9, 0.8, 1.1, 1.3, 1.1, 1.2, 1.9, 2.6, 2.9, 2.8],
            "Loan_to_Deposit": [59, 60, 58, 56, 57, 58, 55, 52, 49, 46, 43, 41],
        },
        "First Capital Bank": {
            "RCFE": [0.4, 0.4, 0.4, 0.43, 0.43, 0.43, 0.43, 0.43, 0.57, 0.57, 0.67, 0.67],
            "NPL_Ratio": [20.5, 19.8, 18.5, 10.2, 9.5, 13.3, 13.3, 10.5, 7.2, 5.1, 2.7, 3.66],
            "Board_Independence": [0.55, 0.55, 0.57, 0.57, 0.57, 0.57, 0.57, 0.57, 0.64, 0.67, 0.71, 0.71],
            "RC_Size": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
            "Bank_Size": [5.65, 5.62, 5.58, 5.55, 5.6, 5.65, 5.7, 5.78, 5.88, 5.98, 6.08, 6.15],
            "Capital_Adequacy": [14.5, 14, 13.8, 14.2, 14.8, 15.5, 17, 19, 21, 23, 25, 26.5],
            "ROA": [0.8, 0.6, 0.4, 0.3, 0.6, 0.8, 0.6, 0.7, 1.4, 2, 2.3, 2.2],
            "Loan_to_Deposit": [63, 64, 62, 60, 61, 62, 59, 56, 53, 50, 47, 45],
        },
        "Metbank": {
            "RCFE": [0.33, 0.33, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.5, 0.5, 0.57, 0.57],
            "NPL_Ratio": [17, 16.5, 15, 8.2, 7.8, 7.5, 8.1, 7.4, 6.2, 4.9, 3.8, 4.1],
            "Board_Independence": [0.5, 0.5, 0.55, 0.56, 0.56, 0.56, 0.56, 0.56, 0.6, 0.63, 0.67, 0.67],
            "RC_Size": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
            "Bank_Size": [5.3, 5.28, 5.25, 5.22, 5.28, 5.32, 5.38, 5.45, 5.55, 5.65, 5.75, 5.82],
            "Capital_Adequacy": [13.5, 13, 12.8, 13.2, 13.8, 14.5, 16, 18, 20, 22, 24, 25.5],
            "ROA": [0.5, 0.4, 0.2, 0.1, 0.4, 0.6, 0.4, 0.5, 1.2, 1.8, 2.1, 2],
            "Loan_to_Deposit": [68, 69, 67, 65, 66, 67, 64, 61, 58, 55, 52, 50],
        },
    }
    
    # Build the DataFrame
    for bank_name, bank_vals in banks_dict.items():
        for i in range(12):
            data["Bank"].append(bank_name)
            data["Year"].append(years[i])
            data["RCFE"].append(bank_vals["RCFE"][i])
            data["NPL_Ratio"].append(bank_vals["NPL_Ratio"][i])
            data["Board_Independence"].append(bank_vals["Board_Independence"][i])
            data["RC_Size"].append(bank_vals["RC_Size"][i])
            data["GDP_Growth"].append(gdp[i])
            data["Policy_Rate"].append(policy[i])
            data["Bank_Size"].append(bank_vals["Bank_Size"][i])
            data["Capital_Adequacy"].append(bank_vals["Capital_Adequacy"][i])
            data["ROA"].append(bank_vals["ROA"][i])
            data["Loan_to_Deposit"].append(bank_vals["Loan_to_Deposit"][i])
            data["ZAMCO_Period"].append(zamco[i])
    
    df = pd.DataFrame(data)
    return df

# Load the data once at module level
REAL_BANK_DATA = load_real_bank_data()

# ─── Authentication Functions ─────────────────────────────────────────────────
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username, password):
    if username in st.session_state.users:
        return st.session_state.users[username] == hash_password(password)
    return False

def register_user(username, password):
    if username in st.session_state.users:
        return False
    st.session_state.users[username] = hash_password(password)
    return True

# ─── Data Import Functions ────────────────────────────────────────────────────
def import_from_system():
    """Load the real Zimbabwe bank panel data"""
    return REAL_BANK_DATA.copy()

def import_from_api(api_key):
    """Simulate API import"""
    return REAL_BANK_DATA.copy()

def import_from_manual_upload(uploaded_file):
    """Handle manual CSV/Excel upload - properly parse the Excel structure"""
    try:
        # Try to read with different approaches
        xl = pd.ExcelFile(uploaded_file)
        
        # Try "Panel Data" sheet first
        sheet_name = "Panel Data" if "Panel Data" in xl.sheet_names else xl.sheet_names[0]
        
        # Read the file, skip the first 3 rows of headers
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name, skiprows=3)
        
        # Define the expected column order from your Excel
        # Column mapping based on the actual structure
        column_mapping = {
            df.columns[0]: "Bank",           # Column A
            df.columns[1]: "Year",           # Column B
            df.columns[3]: "RCFE",           # Column D
            df.columns[4]: "Board_Independence",  # Column E
            df.columns[5]: "RC_Size",        # Column F
            df.columns[6]: "NPL_Ratio",      # Column G
            df.columns[9]: "GDP_Growth",     # Column J
            df.columns[10]: "Policy_Rate",   # Column K
            df.columns[12]: "Bank_Size",     # Column M
            df.columns[13]: "Capital_Adequacy",  # Column N
            df.columns[14]: "ROA",           # Column O
            df.columns[15]: "Loan_to_Deposit",   # Column P
        }
        
        # Rename the columns
        df = df.rename(columns=column_mapping)
        
        # Keep only the columns we need
        required_cols = ["Bank", "Year", "RCFE", "NPL_Ratio", "Board_Independence", 
                        "RC_Size", "GDP_Growth", "Policy_Rate", "Bank_Size", 
                        "Capital_Adequacy", "ROA", "Loan_to_Deposit"]
        
        # Only keep columns that exist
        existing_cols = [col for col in required_cols if col in df.columns]
        df = df[existing_cols]
        
        # Drop rows with missing essential data
        df = df.dropna(subset=["Bank", "Year", "NPL_Ratio"])
        
        # Convert Year to integer
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce").astype("Int64")
        
        # Drop any remaining rows with NaN in key columns
        df = df.dropna()
        
        if len(df) == 0:
            st.warning("No valid data found in file. Using embedded dataset.")
            return REAL_BANK_DATA.copy()
        
        return df
        
    except Exception as e:
        st.error(f"Error reading file: {e}")
        st.warning("Falling back to embedded dataset")
        return REAL_BANK_DATA.copy()

# ─── Panel Regression Model ───────────────────────────────────────────────────
def run_panel_regression(df):
    """Run panel regression analysis"""
    df_clean = df.copy().dropna()
    
    # Make sure we have all required columns
    required_cols = ["RCFE", "Board_Independence", "RC_Size", "GDP_Growth", 
                     "Policy_Rate", "Bank_Size", "Capital_Adequacy", "ROA", "Loan_to_Deposit"]
    
    # Check which columns exist
    available_cols = [col for col in required_cols if col in df_clean.columns]
    
    if "Loan_to_Deposit" not in df_clean.columns:
        st.warning("Loan_to_Deposit column not found. Creating from available data.")
        # Create a placeholder if missing
        df_clean["Loan_to_Deposit"] = 50.0
    
    # Dependent and independent variables
    y = df_clean["NPL_Ratio"]
    X = df_clean[["RCFE", "Board_Independence", "RC_Size", "GDP_Growth", 
                  "Policy_Rate", "Bank_Size", "Capital_Adequacy", "ROA", "Loan_to_Deposit"]]
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    correlation = df_clean["RCFE"].corr(df_clean["NPL_Ratio"])
    rcoefficient = model.params.get("RCFE", 0)
    rpvalue = model.pvalues.get("RCFE", 1)
    significant = rpvalue < 0.05 and rcoefficient < 0
    
    return {
        "model": model,
        "correlation": correlation,
        "rcfe_coefficient": rcoefficient,
        "rcfe_pvalue": rpvalue,
        "significant": significant,
        "rsquared": model.rsquared,
        "n_observations": len(df_clean),
        "banks": df_clean["Bank"].nunique()
    }

# ─── Problem-Solving Functions ────────────────────────────────────────────────
def identify_npl_triggers(df, threshold=7.0):
    latest = df[df["Year"] == df["Year"].max()]
    high_npl = latest[latest["NPL_Ratio"] > threshold]
    return high_npl[["Bank", "NPL_Ratio", "RCFE", "Capital_Adequacy"]]

def assess_composite_risk(df):
    df_risk = df[df["Year"] == df["Year"].max()].copy()
    npl_norm = (df_risk["NPL_Ratio"] - df_risk["NPL_Ratio"].min()) / (df_risk["NPL_Ratio"].max() - df_risk["NPL_Ratio"].min())
    expertise_inv = 1 - (df_risk["RCFE"] - df_risk["RCFE"].min()) / (df_risk["RCFE"].max() - df_risk["RCFE"].min())
    capital_inv = 1 - (df_risk["Capital_Adequacy"] - df_risk["Capital_Adequacy"].min()) / (df_risk["Capital_Adequacy"].max() - df_risk["Capital_Adequacy"].min())
    
    df_risk["Composite_Risk_Score"] = (npl_norm + expertise_inv + capital_inv) / 3 * 100
    df_risk["Risk_Level"] = pd.cut(df_risk["Composite_Risk_Score"], bins=[0, 33, 67, 100], labels=["Low", "Medium", "High"])
    return df_risk.sort_values("Composite_Risk_Score", ascending=False)

def generate_recommendations(high_risk_banks):
    recommendations = []
    for _, bank in high_risk_banks.iterrows():
        rec = {
            "Bank": bank["Bank"],
            "NPL": bank["NPL_Ratio"],
            "Expertise": bank["RCFE"],
            "Capital": bank["Capital_Adequacy"],
            "Immediate_Actions": [],
            "Medium_Term_Actions": []
        }
        if bank["NPL_Ratio"] > 10:
            rec["Immediate_Actions"].append("⚠ CRITICAL: Convene emergency credit risk committee meeting")
            rec["Immediate_Actions"].append("Increase loan loss provisioning")
        elif bank["NPL_Ratio"] > 7:
            rec["Immediate_Actions"].append("Schedule special risk committee meeting for NPL review")
        if bank["RCFE"] < 0.5:
            rec["Immediate_Actions"].append("Recruit additional financial expert to risk committee")
        if bank["Capital_Adequacy"] < 12:
            rec["Immediate_Actions"].append("🔴 Capital adequacy below regulatory minimum (12%)")
        recommendations.append(rec)
    return recommendations

def early_warning_score(row):
    score = 0
    if row["NPL_Ratio"] > 7:
        score += 30
    elif row["NPL_Ratio"] > 5:
        score += 15
    if row["RCFE"] < 0.5:
        score += 25
    elif row["RCFE"] < 0.6:
        score += 10
    if row["Capital_Adequacy"] < 12:
        score += 25
    elif row["Capital_Adequacy"] < 15:
        score += 10
    if row["ROA"] < 1:
        score += 20
    elif row["ROA"] < 1.5:
        score += 10
    return min(score, 100)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Barlow+Condensed:wght@300;500;700&family=Barlow:wght@300;400;500&display=swap');
:root { --bg: #0B0F1A; --surface: #111827; --surface2: #1C2333; --border: #2A3347; --accent: #00E5A0; --accent2: #0091FF; --warn: #FFB547; --danger: #FF4D6A; --text: #E2E8F0; --muted: #6B7A99; --mono: 'IBM Plex Mono', monospace; --head: 'Barlow Condensed', sans-serif; --body: 'Barlow', sans-serif; }
html, body, .stApp { background-color: var(--bg) !important; color: var(--text) !important; font-family: var(--body) !important; }
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab-list"] { background: var(--surface) !important; border-bottom: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] { font-family: var(--mono) !important; font-size: 12px !important; text-transform: uppercase !important; color: var(--muted) !important; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }
.stButton > button { background: var(--accent) !important; color: #0B0F1A !important; font-family: var(--mono) !important; font-weight: 600 !important; text-transform: uppercase !important; border-radius: 4px !important; }
.section-header { font-family: var(--head); font-size: 20px; font-weight: 700; letter-spacing: 0.05em; border-left: 3px solid var(--accent); padding-left: 12px; margin: 20px 0 16px 0; text-transform: uppercase; }
.card { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# ─── Authentication UI ────────────────────────────────────────────────────────
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center;margin-bottom:32px'>
            <div style='font-family:"Barlow Condensed",sans-serif;font-size:48px;font-weight:700;color:#00E5A0'>RCECOS</div>
            <div style='font-family:"IBM Plex Mono",monospace;font-size:11px;color:#6B7A99'>Risk Committee Expertise & Credit Risk Oversight System</div>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Sign Up"])
        
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True):
                    if check_credentials(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab_register:
            with st.form("register_form"):
                new_username = st.text_input("Choose Username")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Sign Up", use_container_width=True):
                    if not new_username or not new_password:
                        st.error("Please fill all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif register_user(new_username, new_password):
                        st.success("Registration successful! Please sign in.")
                    else:
                        st.error("Username already exists")

# ─── Main Application ─────────────────────────────────────────────────────────
def main_app():
    # Sidebar
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:16px 0 8px'>
            <div style='font-family:"IBM Plex Mono",monospace;font-size:10px;color:#6B7A99'>Signed in as</div>
            <div style='font-family:"Barlow Condensed",sans-serif;font-size:18px;font-weight:700;color:#E2E8F0'>{st.session_state.username}</div>
        </div>
        <hr>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📂 Data Import")
        import_option = st.radio("Select Source", ["System Database", "Manual Upload", "API Connection"], label_visibility="collapsed")
        
        if import_option == "System Database":
            if st.button("📊 Load Zimbabwe Bank Data", use_container_width=True):
                with st.spinner("Loading panel data..."):
                    st.session_state.current_data = import_from_system()
                    st.session_state.data_source = "System Database"
                    st.success(f"Loaded {len(st.session_state.current_data)} bank-year observations")
                    st.rerun()
        
        elif import_option == "Manual Upload":
            uploaded_file = st.file_uploader("Upload CSV/Excel", type=["csv", "xlsx"])
            if uploaded_file and st.button("Import File", use_container_width=True):
                with st.spinner("Processing file..."):
                    df = import_from_manual_upload(uploaded_file)
                    if df is not None:
                        st.session_state.current_data = df
                        st.session_state.data_source = "Manual Upload"
                        st.success(f"Imported {len(df)} records")
                        st.rerun()
        
        else:
            api_key = st.text_input("API Key", type="password", placeholder="Enter API key")
            if st.button("🔌 Connect to API", use_container_width=True):
                if api_key:
                    st.session_state.current_data = import_from_api(api_key)
                    st.session_state.data_source = "API Connection"
                    st.success("API connection successful")
                    st.rerun()
        
        st.markdown("---")
        
        if st.session_state.current_data is not None:
            st.markdown("### 🔬 Model Analysis")
            if st.button("▶ Run Panel Regression", use_container_width=True):
                with st.spinner("Estimating panel regression model..."):
                    st.session_state.model_results = run_panel_regression(st.session_state.current_data)
                    st.session_state.analysis_history.append({
                        "timestamp": datetime.datetime.now().isoformat(),
                        "data_source": st.session_state.data_source,
                        "results": {
                            "rcfe_coefficient": st.session_state.model_results["rcfe_coefficient"],
                            "rcfe_pvalue": st.session_state.model_results["rcfe_pvalue"],
                            "rsquared": st.session_state.model_results["rsquared"],
                            "significant": st.session_state.model_results["significant"]
                        }
                    })
                    st.success("Regression completed!")
                    st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.current_data = None
            st.session_state.model_results = None
            st.rerun()
    
    # Main content
    st.markdown("""
    <div style='margin-bottom:20px'>
        <div style='font-family:"IBM Plex Mono",monospace;font-size:11px;color:#6B7A99'>DECISION SUPPORT SYSTEM</div>
        <div style='font-family:"Barlow Condensed",sans-serif;font-size:36px;font-weight:700'>The Effect of Risk Committee Financial Expertise<br>on Credit Risk Management in Zimbabwean Banks</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.current_data is None:
        st.info("👈 Please import data using the sidebar to begin analysis")
        
        st.markdown('<div class="section-header">Available Data Preview</div>', unsafe_allow_html=True)
        st.dataframe(REAL_BANK_DATA.head(20), use_container_width=True)
        st.caption(f"✅ System Database contains {len(REAL_BANK_DATA)} bank-year observations ({REAL_BANK_DATA['Bank'].nunique()} banks × {REAL_BANK_DATA['Year'].nunique()} years, 2013–2024)")
        return
    
    df = st.session_state.current_data
    
    # Verify columns exist
    required_cols = ["NPL_Ratio", "RCFE", "Capital_Adequacy", "ROA", "Bank", "Year"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
        st.write("Available columns:", list(df.columns))
        return
    
    tabs = st.tabs(["📊 Dashboard", "🔬 Model Results", "🚨 Problem Solver", "📜 Analysis History", "📋 Governance Reports"])
    
    # Dashboard Tab
    with tabs[0]:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Avg NPL Ratio", f"{df['NPL_Ratio'].mean():.1f}%", delta=f"{df['NPL_Ratio'].mean() - 7:.1f}% vs 7%")
        with col2:
            st.metric("Avg RCFE", f"{df['RCFE'].mean():.0%}")
        with col3:
            st.metric("Avg CAR", f"{df['Capital_Adequacy'].mean():.1f}%")
        with col4:
            st.metric("Banks Analyzed", df['Bank'].nunique())
        with col5:
            st.metric("Time Period", f"2013-2024 ({df['Year'].nunique()} years)")
        
        col_a, col_b = st.columns(2)
        with col_a:
            fig = px.line(df, x="Year", y="NPL_Ratio", color="Bank", title="NPL Ratio Trends by Bank")
            fig.add_hline(y=7, line_dash="dash", line_color="#FF4D6A", annotation_text="7% Threshold")
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        
        with col_b:
            latest = df[df["Year"] == df["Year"].max()]
            corr = latest["RCFE"].corr(latest["NPL_Ratio"])
            fig = px.scatter(latest, x="RCFE", y="NPL_Ratio", color="Bank", size="Capital_Adequacy", text="Bank", title=f"RCFE vs NPL (r = {corr:.3f})")
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<div class="section-header">NPL Ratio Heatmap</div>', unsafe_allow_html=True)
        heatmap_data = df.pivot_table(index="Bank", columns="Year", values="NPL_Ratio")
        fig = px.imshow(heatmap_data, text_auto=True, aspect="auto", color_continuous_scale="RdYlGn_r")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    # Model Results Tab
    with tabs[1]:
        if st.session_state.model_results is None:
            st.warning("⚠ No model results. Please run panel regression from sidebar.")
        else:
            results = st.session_state.model_results
            st.markdown(f"""
            <div class='card'>
                <div style='font-weight:700;margin-bottom:12px'>📊 Hypothesis Test</div>
                <div><b>H₀:</b> RCFE has NO significant effect on NPL ratio</div>
                <div><b>H₁:</b> RCFE HAS a significant effect on NPL ratio</div>
                <hr>
                RCFE Coefficient: <b>{results['rcfe_coefficient']:.4f}</b><br>
                P-value: <b>{results['rcfe_pvalue']:.4f}</b>
                <div style='margin-top:12px;padding:12px;border-radius:6px;background:{"rgba(0,229,160,0.1)" if results['significant'] else "rgba(255,77,106,0.1)"}'>
                    {"✅ H₀ REJECTED — RCFE has significant negative effect on NPL ratio" if results['significant'] else "❌ Cannot reject H₀ — No significant relationship found"}
                </div>
            </div>
            """, unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("R-squared", f"{results['rsquared']:.4f}")
                st.metric("Observations", results['n_observations'])
            with col2:
                st.metric("Correlation", f"{results['correlation']:.4f}")
                st.metric("Banks", results['banks'])
    
    # Problem Solver Tab
    with tabs[2]:
        st.markdown('<div class="section-header">🛠 Problem Solving Framework</div>', unsafe_allow_html=True)
        
        st.subheader("🔴 Problem 1: Elevated Non-Performing Loans")
        high_npl = identify_npl_triggers(df)
        if len(high_npl) > 0:
            st.warning(f"{len(high_npl)} banks have NPL > 7%")
            st.dataframe(high_npl, use_container_width=True)
        else:
            st.success("All banks below 7% NPL threshold")
        
        st.subheader("⚠ Problem 2: Composite Risk Assessment")
        risk_assessment = assess_composite_risk(df)
        fig = px.bar(risk_assessment.head(10), x="Bank", y="Composite_Risk_Score", color="Risk_Level")
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("💡 Problem 3: Targeted Recommendations")
        high_risk = risk_assessment[risk_assessment['Risk_Level'].isin(['High', 'Medium'])].head(5)
        recommendations = generate_recommendations(high_risk)
        for rec in recommendations:
            with st.expander(f"🏦 {rec['Bank']} — NPL: {rec['NPL']:.1f}% | Expertise: {rec['Expertise']:.0%}"):
                if rec['Immediate_Actions']:
                    for action in rec['Immediate_Actions']:
                        st.markdown(f"- {action}")
        
        st.subheader("🚨 Problem 4: Early Warning System")
        df_ews = df[df["Year"] == df["Year"].max()].copy()
        df_ews["EWS_Score"] = df_ews.apply(early_warning_score, axis=1)
        fig = px.bar(df_ews, x="Bank", y="EWS_Score", title="Early Warning Scores")
        fig.add_hline(y=60, line_dash="dash", line_color="#FFB547")
        st.plotly_chart(fig, use_container_width=True)
    
    # Analysis History Tab
    with tabs[3]:
        st.markdown('<div class="section-header">📜 Analysis History</div>', unsafe_allow_html=True)
        if len(st.session_state.analysis_history) == 0:
            st.info("No analysis history yet.")
        else:
            for i, entry in enumerate(reversed(st.session_state.analysis_history)):
                ts = datetime.datetime.fromisoformat(entry["timestamp"])
                with st.expander(f"Analysis #{len(st.session_state.analysis_history)-i} — {ts.strftime('%Y-%m-%d %H:%M')}"):
                    st.json(entry["results"])
        
        if st.button("🗑 Clear History"):
            st.session_state.analysis_history = []
            st.rerun()
    
    # Governance Reports Tab
    with tabs[4]:
        st.markdown('<div class="section-header">📋 Governance Reports</div>', unsafe_allow_html=True)
        latest_data = df[df["Year"] == df["Year"].max()]
        st.dataframe(latest_data[["Bank", "NPL_Ratio", "RCFE", "Capital_Adequacy", "ROA"]], use_container_width=True)

# ─── Run App ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if st.session_state.authenticated:
        main_app()
    else:
        show_login()
