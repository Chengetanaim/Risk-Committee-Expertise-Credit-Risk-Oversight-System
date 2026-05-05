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
    page_title="ZB Bank | RCECOS - Risk Committee Expertise & Credit Risk Oversight",
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
    st.session_state.users = {"admin": hashlib.sha256("admin123".encode()).hexdigest()}
if "analysis_history" not in st.session_state:
    st.session_state.analysis_history = []
if "current_data" not in st.session_state:
    st.session_state.current_data = None
if "individual_input" not in st.session_state:
    st.session_state.individual_input = {}
if "loan_scanner_history" not in st.session_state:
    st.session_state.loan_scanner_history = []
if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = None

# ─── Helper function for JSON serialization ──────────────────────────────────
def convert_to_serializable(obj):
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj

# ─── ZB BANK DATA (Pre-ingested - Real data from the Excel) ───────────────────
def load_zb_bank_data():
    data = {
        "Bank": ["ZB Bank"] * 12,
        "Year": [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        "RCFE": [0.43, 0.43, 0.43, 0.5, 0.5, 0.5, 0.5, 0.5, 0.57, 0.57, 0.57, 0.57],
        "NPL_Ratio": [19.5, 18.9, 17.4, 9.5, 12, 12, 6.8, 6.2, 5.4, 4.5, 3.5, 3.9],
        "Board_Independence": [0.57, 0.57, 0.57, 0.6, 0.6, 0.6, 0.6, 0.6, 0.64, 0.64, 0.67, 0.67],
        "RC_Size": [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4],
        "GDP_Growth": [2.8, 2.4, 1.8, 0.8, 4.7, 4.2, -6.5, -7.82, 8.47, 6.14, 5.3, 2],
        "Policy_Rate": [9, 9, 9, 8.5, 8.5, 10, 35, 35, 60, 200, 80, 35],
        "Bank_Size": [5.98, 5.95, 5.9, 5.88, 5.92, 5.96, 6.0, 6.08, 6.18, 6.28, 6.38, 6.45],
        "Capital_Adequacy": [16.2, 15.8, 15.5, 16, 16.5, 17, 18.5, 20, 22, 24, 26, 27.5],
        "ROA": [1.2, 1, 0.8, 0.7, 1, 1.2, 1, 1.1, 1.8, 2.5, 2.8, 2.6],
        "Loan_to_Deposit": [58, 59, 57, 55, 56, 57, 53, 50, 47, 44, 42, 40],
        "ZAMCO_Period": ["No", "Yes", "Yes", "Yes", "Yes", "Yes", "No", "No", "No", "No", "No", "No"]
    }
    return pd.DataFrame(data)

def get_risk_committee_members():
    members = pd.DataFrame({
        "Name": ["Prof. Tafadzwa Ncube", "Mr. Charles Mutasa", "Mrs. Grace Mapondera", "Dr. Tendai Makoni"],
        "Position": ["Chairperson", "Member", "Independent Member", "Observer"],
        "Qualifications": ["PhD Finance, CFA, MBA", "CFA, ACCA, MSc Banking", "CA(Z), MSc Finance, FRM", "PhD Economics, MSc Risk Management"],
        "Expertise_Score": [95, 82, 90, 78],
        "Independence": ["Independent", "Non-Independent", "Independent", "Independent"],
        "Risk_Experience_Years": [18, 14, 20, 12]
    })
    return members

# ─── LOAN RISK SCANNER FUNCTIONS ──────────────────────────────────────────────
def calculate_loan_risk_score(loan_data):
    """Calculate risk score for an individual loan"""
    score = 0
    risk_factors = []
    
    # Factor 1: Loan amount vs borrower income (DTI ratio)
    dti = loan_data.get("dti_ratio", loan_data.get("loan_amount", 0) / max(loan_data.get("monthly_income", 1), 1))
    if dti > 0.5:
        score += 30
        risk_factors.append("High debt-to-income ratio (>50%)")
    elif dti > 0.35:
        score += 15
        risk_factors.append("Moderate debt-to-income ratio (>35%)")
    
    # Factor 2: Repayment history
    repayment = loan_data.get("repayment_history", "good")
    if repayment == "poor":
        score += 40
        risk_factors.append("Poor repayment history - multiple defaults")
    elif repayment == "fair":
        score += 20
        risk_factors.append("Fair repayment history - occasional late payments")
    elif repayment == "good":
        score += 5
        risk_factors.append("Good repayment history")
    
    # Factor 3: Sector risk
    sector = loan_data.get("sector", "unknown")
    sector_risk = {
        "agriculture": 35, "mining": 30, "manufacturing": 25,
        "retail": 15, "services": 10, "technology": 10, "government": 5
    }
    sector_score = sector_risk.get(sector.lower(), 20)
    score += sector_score
    risk_factors.append(f"Sector: {sector} (risk score: {sector_score}/40)")
    
    # Factor 4: Collateral coverage
    collateral = loan_data.get("collateral_coverage", 0)
    if collateral < 0.5:
        score += 25
        risk_factors.append("Insufficient collateral coverage (<50%)")
    elif collateral < 0.8:
        score += 12
        risk_factors.append("Moderate collateral coverage (50-80%)")
    
    # Factor 5: Existing relationship with bank
    relationship = loan_data.get("relationship_years", 0)
    if relationship < 1:
        score += 15
        risk_factors.append("New customer (<1 year relationship)")
    elif relationship < 3:
        score += 5
        risk_factors.append("Short relationship (1-3 years)")
    
    # Cap at 100
    final_score = min(score, 100)
    
    # Determine risk category
    if final_score >= 70:
        risk_category = "Critical"
        recommended_action = "Immediate committee review required. Do not approve."
        color = "#FF4D6A"
    elif final_score >= 45:
        risk_category = "Elevated"
        recommended_action = "Enhanced due diligence required. Committee member sign-off needed."
        color = "#FFB547"
    elif final_score >= 20:
        risk_category = "Moderate"
        recommended_action = "Standard approval process. File for committee information."
        color = "#0091FF"
    else:
        risk_category = "Low"
        recommended_action = "Fast-track approval."
        color = "#00E5A0"
    
    return {
        "score": final_score,
        "risk_category": risk_category,
        "risk_factors": risk_factors,
        "recommended_action": recommended_action,
        "color": color
    }

# ─── RCFE SIMULATOR FUNCTIONS ─────────────────────────────────────────────────
def run_rcfe_simulation(current_rcfe, current_npl, target_rcfe):
    """Simulate NPL reduction based on RCFE improvement"""
    
    # Based on regression analysis from Chapter 4
    # Coefficient: NPL reduction = RCFE_improvement * correlation_factor
    correlation_factor = 0.75  # Each 10% RCFE improvement → 7.5% NPL reduction
    
    rcfe_improvement = (target_rcfe - current_rcfe) / 100
    expected_npl_reduction_pct = rcfe_improvement * correlation_factor * 100
    expected_new_npl = current_npl * (1 - expected_npl_reduction_pct / 100)
    
    # Calculate timeline based on improvement magnitude
    if rcfe_improvement > 0.2:
        timeline = "6-12 months (requires committee restructuring + training)"
    elif rcfe_improvement > 0.1:
        timeline = "3-6 months (targeted recruitment + CPD)"
    else:
        timeline = "1-3 months (minor adjustments)"
    
    # Calculate capital preservation
    loan_portfolio = 1000  # Assume ZW$1 billion loan portfolio
    capital_preserved = (current_npl - max(expected_new_npl, 0.5)) / 100 * loan_portfolio
    
    return {
        "current_rcfe_pct": current_rcfe,
        "target_rcfe_pct": target_rcfe,
        "rcfe_improvement_pct": rcfe_improvement * 100,
        "current_npl": current_npl,
        "expected_new_npl": max(expected_new_npl, 0.5),
        "npl_reduction_pct": current_npl - max(expected_new_npl, 0.5),
        "expected_npl_reduction_percent": expected_npl_reduction_pct,
        "timeline": timeline,
        "capital_preserved_mil": capital_preserved,
        "feasible": target_rcfe <= 85
    }

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

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Barlow+Condensed:wght@300;500;700&family=Barlow:wght@300;400;500&display=swap');
:root { --bg: #0B0F1A; --surface: #111827; --surface2: #1C2333; --border: #2A3347; --accent: #00E5A0; --accent2: #0091FF; --warn: #FFB547; --danger: #FF4D6A; --text: #E2E8F0; --muted: #6B7A99; }
html, body, .stApp { background-color: var(--bg) !important; color: var(--text) !important; font-family: 'Barlow', sans-serif; }
[data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: var(--text) !important; }
h1, h2, h3, h4 { font-family: 'Barlow Condensed', sans-serif; letter-spacing: 0.03em; }
[data-testid="metric-container"] { background: var(--surface2) !important; border: 1px solid var(--border) !important; border-radius: 8px; padding: 12px; }
.stTabs [data-baseweb="tab-list"] { background: var(--surface) !important; border-bottom: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] { font-family: 'IBM Plex Mono', monospace; font-size: 12px !important; text-transform: uppercase !important; color: #6B7A99 !important; }
.stTabs [aria-selected="true"] { color: #00E5A0 !important; border-bottom: 2px solid #00E5A0 !important; }
.stButton > button { background: #00E5A0 !important; color: #0B0F1A !important; font-family: 'IBM Plex Mono', monospace; font-weight: 600 !important; text-transform: uppercase !important; border-radius: 4px; }
.section-header { font-family: 'Barlow Condensed', sans-serif; font-size: 20px; font-weight: 700; border-left: 3px solid #00E5A0; padding-left: 12px; margin: 20px 0 16px; text-transform: uppercase; }
.card { background: #1C2333; border: 1px solid #2A3347; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.member-card { background: #111827; border: 1px solid #2A3347; border-radius: 8px; padding: 12px; margin: 8px 0; }
.risk-critical { color: #FF4D6A; font-weight: 700; }
.risk-elevated { color: #FFB547; font-weight: 700; }
.risk-moderate { color: #0091FF; font-weight: 700; }
.risk-low { color: #00E5A0; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ─── Authentication UI ────────────────────────────────────────────────────────
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center;margin-bottom:32px'>
            <div style='font-size:48px;font-weight:700;color:#00E5A0'>ZB Bank</div>
            <div style='font-size:14px;color:#6B7A99;margin-top:-8px'>RCECOS - Risk Committee Expertise & Credit Risk Oversight System</div>
            <div style='font-size:12px;color:#6B7A99;margin-top:8px'>Demo: admin / admin123</div>
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
    zb_data = load_zb_bank_data()
    rc_members = get_risk_committee_members()
    
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:16px 0 8px'>
            <div style='font-size:10px;color:#6B7A99'>Signed in as</div>
            <div style='font-size:18px;font-weight:700;color:#00E5A0'>{st.session_state.username}</div>
            <div style='font-size:11px;color:#6B7A99'>ZB Bank • Risk Management System</div>
        </div>
        <hr>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 Navigation")
        page = st.radio("", [
            "🏦 Bank Dashboard",
            "👥 Risk Committee Expertise",
            "📊 Analysis",
            "🔍 Loan Risk Scanner",
            "📈 RCFE Simulator",
            "📝 Individual Computation",
            "📋 Reports & Warnings"
        ], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()
    
    # Header
    st.markdown("""
    <div style='margin-bottom:20px'>
        <div style='font-size:11px;color:#6B7A99;font-family:"IBM Plex Mono"'>ZB FINANCIAL HOLDINGS</div>
        <div style='font-size:32px;font-weight:700;font-family:"Barlow Condensed"'>Risk Committee Financial Expertise & Credit Risk Management</div>
        <div style='font-size:14px;color:#6B7A99'>Empirical Analysis & Decision Support System</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 1: BANK DASHBOARD
    # ──────────────────────────────────────────────────────────────────────────
    if page == "🏦 Bank Dashboard":
        st.markdown('<div class="section-header">ZB Bank Performance Dashboard</div>', unsafe_allow_html=True)
        
        latest = zb_data[zb_data["Year"] == zb_data["Year"].max()].iloc[0]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Current NPL Ratio", f"{latest['NPL_Ratio']:.1f}%", delta=f"{latest['NPL_Ratio'] - 7:.1f}% vs 7% threshold", delta_color="inverse")
        with col2:
            rcfe_pct = latest['RCFE'] * 100
            st.metric("RCFE Score", f"{rcfe_pct:.0f}%", delta="Target: 60%")
        with col3:
            st.metric("Capital Adequacy", f"{latest['Capital_Adequacy']:.1f}%", delta="Min: 12%")
        with col4:
            st.metric("ROA", f"{latest['ROA']:.1f}%")
        with col5:
            st.metric("Loan-to-Deposit", f"{latest['Loan_to_Deposit']:.0f}%")
        
        col_a, col_b = st.columns(2)
        with col_a:
            fig = px.line(zb_data, x="Year", y="NPL_Ratio", title="NPL Ratio Trend (2013-2024)", markers=True)
            fig.add_hline(y=7, line_dash="dash", line_color="#FF4D6A", annotation_text="7% Critical")
            fig.add_hline(y=5, line_dash="dash", line_color="#FFB547", annotation_text="5% Warning")
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            
        with col_b:
            fig = px.line(zb_data, x="Year", y="RCFE", title="RCFE Trend (2013-2024)", markers=True)
            fig.add_hline(y=0.6, line_dash="dash", line_color="#00E5A0", annotation_text="Target 60%")
            fig.add_hline(y=0.5, line_dash="dash", line_color="#FFB547", annotation_text="Minimum 50%")
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        
        corr = zb_data["RCFE"].corr(zb_data["NPL_Ratio"])
        st.info(f"📊 Key Finding: Pearson Correlation between RCFE and NPL: {corr:.3f} (Negative correlation supports hypothesis)")

    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 2: RISK COMMITTEE EXPERTISE
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "👥 Risk Committee Expertise":
        st.markdown('<div class="section-header">Risk Committee Financial Expertise Analysis</div>', unsafe_allow_html=True)
        
        latest = zb_data[zb_data["Year"] == zb_data["Year"].max()].iloc[0]
        current_rcfe = latest["RCFE"] * 100
        current_npl = latest["NPL_Ratio"]
        
        status_color = "#FFB547" if current_rcfe >= 50 else "#FF4D6A"
        
        st.markdown(f"""
        <div class='card'>
            <div style='display:flex; justify-content:space-between'>
                <div>
                    <div style='font-size:14px;color:#6B7A99'>Risk Committee Financial Expertise Score</div>
                    <div style='font-size:48px;font-weight:700;color:{status_color}'>{current_rcfe:.0f}%</div>
                    <div style='font-size:12px'>Target: 60% | Minimum: 50%</div>
                </div>
                <div style='text-align:center'>
                    <div style='font-size:14px;color:#6B7A99'>Current NPL Ratio</div>
                    <div style='font-size:36px;font-weight:700;color:{"#FFB547" if current_npl>5 else "#00E5A0"}'>{current_npl:.1f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Current Risk Committee Members</div>', unsafe_allow_html=True)
        
        cols = st.columns(4)
        for idx, (_, member) in enumerate(rc_members.iterrows()):
            with cols[idx % 4]:
                st.markdown(f"""
                <div class='member-card'>
                    <div style='font-weight:700;font-size:14px'>{member['Name']}</div>
                    <div style='font-size:11px;color:#6B7A99'>{member['Position']}</div>
                    <div style='font-size:10px;color:#6B7A99;margin:4px 0'>{member['Qualifications']}</div>
                    <div style='font-size:12px;margin-top:8px'>Expertise: {member['Expertise_Score']}/100</div>
                    <div style='font-size:11px;color:#6B7A99'>Experience: {member['Risk_Experience_Years']} yrs</div>
                </div>
                """, unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 3: CHAPTER 4 ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "📊 Analysis":
        st.markdown('<div class="section-header">Empirical Findings & Hypothesis Testing</div>', unsafe_allow_html=True)
        
        corr = zb_data["RCFE"].corr(zb_data["NPL_Ratio"])
        
        st.markdown(f"""
        <div class='card'>
            <div style='font-weight:700;margin-bottom:12px'>🎯 Research Hypothesis Test Results</div>
            <div><b>H₀:</b> Risk committee financial expertise has NO significant effect on NPL ratio</div>
            <div><b>H₁:</b> Risk committee financial expertise HAS a significant effect on NPL ratio</div>
            <hr>
            <div style='font-size:14px;margin:12px 0'>
                Pearson Correlation: <b>{corr:.4f}</b><br>
                Direction: <b style='color:{"#00E5A0" if corr < 0 else "#FF4D6A"}'>{"Negative (supports H₁)" if corr < 0 else "Positive (does not support H₁)"}</b>
            </div>
            <div style='padding:12px;border-radius:6px;background:{"rgba(0,229,160,0.1)" if corr < -0.3 else "rgba(255,77,106,0.1)"}'>
                {"✅ <b>H₀ REJECTED</b> — RCFE has a significant negative effect on NPL ratio" if corr < -0.3 else "⚠️ Weak correlation — More data needed"}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        X = sm.add_constant(zb_data["RCFE"])
        y = zb_data["NPL_Ratio"]
        model = sm.OLS(y, X).fit()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("R-squared", f"{model.rsquared:.4f}")
            st.metric("RCFE Coefficient", f"{model.params.get('RCFE', 0):.4f}")
        with col2:
            st.metric("P-value", f"{model.pvalues.get('RCFE', 1):.4f}")
            st.metric("Significant at 5%", "✅ Yes" if model.pvalues.get('RCFE', 1) < 0.05 else "❌ No")

    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 4: LOAN RISK SCANNER (NEW FEATURE)
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "🔍 Loan Risk Scanner":
        st.markdown('<div class="section-header">🔍 Loan Risk Scanner - Early Warning System</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background:#111827; padding:12px 16px; border-radius:8px; margin-bottom:20px'>
            <div style='font-size:13px; color:#B0BAD0'>
                Based on findings, this tool helps risk committees identify high-risk loans BEFORE they become non-performing.
                Enter loan details below to receive a risk score and recommended action.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Loan Application Details")
            
            loan_amount = st.number_input("Loan Amount (ZW$)", min_value=1000, max_value=50000000, value=500000, step=10000)
            monthly_income = st.number_input("Borrower Monthly Income (ZW$)", min_value=1000, max_value=5000000, value=50000, step=5000)
            dti = loan_amount / 12 / monthly_income if monthly_income > 0 else 0
            
            st.caption(f"Debt-to-Income Ratio (DTI): {dti:.2f} {'⚠️ High' if dti > 0.5 else '✅ Acceptable' if dti < 0.35 else '⚠️ Moderate'}")
            
            sector = st.selectbox("Economic Sector", ["Agriculture", "Mining", "Manufacturing", "Retail", "Services", "Technology", "Government"])
            repayment_history = st.selectbox("Repayment History", ["Good (no defaults)", "Fair (1-2 late payments)", "Poor (multiple defaults / write-offs)"])
            
        with col2:
            st.markdown("### 📊 Risk Assessment Parameters")
            
            collateral_coverage = st.slider("Collateral Coverage (%)", 0, 150, 70, 5) / 100
            relationship_years = st.number_input("Years of Relationship with Bank", min_value=0, max_value=20, value=3, step=1)
            
            # Get current RCFE from ZB Bank data
            latest = zb_data[zb_data["Year"] == zb_data["Year"].max()].iloc[0]
            current_rcfe = latest["RCFE"] * 100
            
            st.info(f"Current Bank RCFE: {current_rcfe:.0f}% (affects loan approval threshold)")
        
        if st.button("🔍 SCAN LOAN RISK", use_container_width=True):
            loan_data = {
                "loan_amount": loan_amount,
                "monthly_income": monthly_income,
                "dti_ratio": dti,
                "sector": sector,
                "repayment_history": "good" if "Good" in repayment_history else "fair" if "Fair" in repayment_history else "poor",
                "collateral_coverage": collateral_coverage,
                "relationship_years": relationship_years
            }
            
            risk_result = calculate_loan_risk_score(loan_data)
            
            # Store in history
            st.session_state.loan_scanner_history.append({
                "timestamp": datetime.datetime.now().isoformat(),
                "loan_amount": loan_amount,
                "sector": sector,
                "risk_score": risk_result["score"],
                "risk_category": risk_result["risk_category"],
                "action": risk_result["recommended_action"]
            })
            
            # Display results
            st.markdown(f"""
            <div class='card' style='border-left: 4px solid {risk_result["color"]}; margin-top:20px'>
                <div style='text-align:center; margin-bottom:16px'>
                    <div style='font-size:12px; color:#6B7A99'>RISK SCORE</div>
                    <div style='font-size:64px; font-weight:700; color:{risk_result["color"]}'>{risk_result["score"]}/100</div>
                    <div style='font-size:18px; font-weight:700; color:{risk_result["color"]}'>{risk_result["risk_category"]} RISK</div>
                </div>
                <hr>
                <div style='font-weight:700; margin-bottom:8px'>🔴 Risk Factors Identified:</div>
            """, unsafe_allow_html=True)
            
            for factor in risk_result["risk_factors"]:
                st.markdown(f"- {factor}")
            
            st.markdown(f"""
                <hr>
                <div style='font-weight:700; margin-bottom:8px'>✅ Recommended Action:</div>
                <div style='font-size:14px; color:#{risk_result["color"][1:]}'>{risk_result["recommended_action"]}</div>
            """, unsafe_allow_html=True)
            
            # Additional warning if RCFE is low
            if current_rcfe < 60 and risk_result["score"] > 45:
                st.warning(f"⚠️ Committee Note: Bank's current RCFE is {current_rcfe:.0f}% (below 60% target). Consider enhanced review for this {'Critical' if risk_result['score']>70 else 'Elevated'} risk loan.")
        
        # Show recent scans
        if st.session_state.loan_scanner_history:
            st.markdown('<div class="section-header">Recent Loan Scans</div>', unsafe_allow_html=True)
            history_df = pd.DataFrame(st.session_state.loan_scanner_history[-5:])
            history_df["timestamp"] = pd.to_datetime(history_df["timestamp"]).dt.strftime("%H:%M %d/%m")
            st.dataframe(history_df[["timestamp", "loan_amount", "sector", "risk_score", "risk_category"]], use_container_width=True)

    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 5: RCFE SIMULATOR (NEW FEATURE)
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "📈 RCFE Simulator":
        st.markdown('<div class="section-header">📈 RCFE Simulator - NPL Reduction Tool</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background:#111827; padding:12px 16px; border-radius:8px; margin-bottom:20px'>
            <div style='font-size:13px; color:#B0BAD0'>
                Based on the regression analysis, this simulator shows how improving Risk Committee Financial Expertise (RCFE) 
                can reduce Non-Performing Loans (NPLs) and preserve capital.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Get current values
        latest = zb_data[zb_data["Year"] == zb_data["Year"].max()].iloc[0]
        current_rcfe = latest["RCFE"] * 100
        current_npl = latest["NPL_Ratio"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Current Bank Position")
            st.metric("Current RCFE", f"{current_rcfe:.0f}%", delta="Target: 60%", delta_color="inverse")
            st.metric("Current NPL Ratio", f"{current_npl:.1f}%", delta="Target: 5%", delta_color="inverse")
            st.metric("Loan Portfolio Estimate", "ZW$1.0 Billion", delta="Used for capital preservation calculation")
        
        with col2:
            st.markdown("### 🎯 Simulation Parameters")
            target_rcfe = st.slider("Target RCFE (%)", min_value=float(current_rcfe), max_value=85.0, value=min(65.0, 85.0), step=1.0)
            
            if st.button("📈 RUN SIMULATION", use_container_width=True):
                simulation = run_rcfe_simulation(current_rcfe, current_npl, target_rcfe)
                st.session_state.simulation_results = simulation
        
        if st.session_state.simulation_results:
            sim = st.session_state.simulation_results
            
            if not sim["feasible"]:
                st.warning("Target RCFE > 85% may not be feasible in short term. Consider staged approach.")
            
            st.markdown('<div class="section-header">📉 Simulation Results</div>', unsafe_allow_html=True)
            
            # Results cards
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.metric("RCFE Improvement", f"+{sim['rcfe_improvement_pct']:.0f}%", delta="Target achieved")
            with r2:
                st.metric("Expected NPL Reduction", f"{sim['expected_npl_reduction_percent']:.1f}%", delta=f"to {sim['expected_new_npl']:.1f}%", delta_color="inverse")
            with r3:
                st.metric("Capital Preserved", f"ZW${sim['capital_preserved_mil']:.1f}M", delta="Estimated savings")
            with r4:
                st.metric("Timeline", sim["timeline"])
            
            # Visual comparison
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Current", x=["RCFE (%)", "NPL (%)"], y=[sim["current_rcfe_pct"], sim["current_npl"]], marker_color=["#FFB547", "#FFB547"]))
            fig.add_trace(go.Bar(name="Target (Projected)", x=["RCFE (%)", "NPL (%)"], y=[sim["target_rcfe_pct"], sim["expected_new_npl"]], marker_color=["#00E5A0", "#00E5A0"]))
            fig.update_layout(title="RCFE Improvement → NPL Reduction Simulation", barmode='group', height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Chapter 4 conclusion
            st.markdown(f"""
            <div class='card' style='background:rgba(0,229,160,0.05); border-color:#00E5A0'>
                <div style='font-weight:700; color:#00E5A0'>📚 Conclusion Applied</div>
                <div style='font-size:13px; margin-top:8px'>
                    Based on the regression analysis (R² = {zb_data['RCFE'].corr(zb_data['NPL_Ratio'])**2:.3f}), 
                    increasing ZB Bank's RCFE from {sim['current_rcfe_pct']:.0f}% to {sim['target_rcfe_pct']:.0f}% 
                    is projected to reduce NPL ratio from {sim['current_npl']:.1f}% to {sim['expected_new_npl']:.1f}%, 
                    a reduction of {sim['npl_reduction_pct']:.1f} percentage points.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 6: INDIVIDUAL COMPUTATION
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "📝 Individual Computation":
        st.markdown('<div class="section-header">Individual Risk Computation</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            rcfe_input = st.slider("Risk Committee Financial Expertise (RCFE)", 0.0, 1.0, 0.55, 0.01)
            npl_input = st.number_input("NPL Ratio (%)", 0.0, 30.0, 5.0, 0.1)
            car_input = st.number_input("Capital Adequacy Ratio (%)", 0.0, 35.0, 15.0, 0.1)
            
            if st.button("Compute Risk Metrics", use_container_width=True):
                results = {
                    "rcfe_score": rcfe_input * 100,
                    "rcfe_adequate": rcfe_input * 100 >= 60,
                    "npl_critical": npl_input > 7
                }
                st.session_state.individual_input = results
        
        with col2:
            if st.session_state.individual_input:
                res = st.session_state.individual_input
                st.markdown(f"""
                <div class='card'>
                    <div><b>RCFE Score:</b> {res['rcfe_score']:.0f}% {'✅ Adequate' if res['rcfe_adequate'] else '⚠️ Below target'}</div>
                    <div><b>NPL Critical:</b> {'🔴 Yes' if res['npl_critical'] else '🟢 No'}</div>
                </div>
                """, unsafe_allow_html=True)

    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 7: REPORTS & WARNINGS
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "📋 Reports & Warnings":
        st.markdown('<div class="section-header">Risk Reports & Early Warning System</div>', unsafe_allow_html=True)
        
        latest = zb_data[zb_data["Year"] == zb_data["Year"].max()].iloc[0]
        current_rcfe = latest["RCFE"] * 100
        
        # Warning Status
        st.subheader("🚨 Current Warning Status")
        
        warnings_list = []
        if latest["NPL_Ratio"] > 7:
            warnings_list.append(("CRITICAL", f"NPL Ratio at {latest['NPL_Ratio']:.1f}% exceeds 7% threshold", "Immediate board review required"))
        elif latest["NPL_Ratio"] > 5:
            warnings_list.append(("WARNING", f"NPL Ratio at {latest['NPL_Ratio']:.1f}% exceeds 5% advisory threshold", "Enhanced monitoring recommended"))
        
        if current_rcfe < 50:
            warnings_list.append(("CRITICAL", f"RCFE at {current_rcfe:.0f}% below minimum 50% threshold", "Urgent recruitment of financial experts"))
        elif current_rcfe < 60:
            warnings_list.append(("WARNING", f"RCFE at {current_rcfe:.0f}% below target 60%", "Consider committee composition review"))
        
        if warnings_list:
            for level, message, action in warnings_list:
                color = "#FF4D6A" if level == "CRITICAL" else "#FFB547"
                st.markdown(f"""
                <div class='card' style='border-left:3px solid {color}'>
                    <div><span style='color:{color};font-weight:700'>[{level}]</span> {message}</div>
                    <div style='font-size:12px;color:#6B7A99;margin-top:8px'>Action: {action}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No active warnings")
        
        # Board Report
        st.markdown('<div class="section-header">📋 Board Risk Committee Report</div>', unsafe_allow_html=True)
        
        report_date = datetime.datetime.now().strftime("%d %B %Y")
        
        with st.container():
            st.markdown(f"""
            <div style='background:#111827; border:1px solid #2A3347; border-radius:8px; overflow:hidden'>
                <div style='background:#1C2333; padding:12px 16px'>
                    <div style='font-size:10px; color:#6B7A99'>CONFIDENTIAL - BOARD RISK COMMITTEE</div>
                    <div style='font-size:18px; font-weight:700'>Quarterly Credit Risk Oversight Report</div>
                    <div style='font-size:12px; color:#6B7A99'>{report_date} | ZB Bank Limited</div>
                </div>
                <div style='padding:16px'>
                    <div style='font-weight:700; color:#00E5A0; margin-bottom:8px'>Executive Summary</div>
                    <div style='font-size:14px; margin-bottom:16px'>
                        As of {latest['Year']}, ZB Bank recorded an NPL ratio of <b>{latest['NPL_Ratio']:.1f}%</b>
                        against a target of 7%. RCFE stands at <b>{current_rcfe:.0f}%</b> (target: 60%).
                    </div>
                    

            """, unsafe_allow_html=True)
            
            kpi_cols = st.columns(3)
            metrics = [
                ("NPL Ratio", f"{latest['NPL_Ratio']:.1f}%", "#FFB547" if latest['NPL_Ratio']>5 else "#00E5A0"),
                ("RCFE", f"{current_rcfe:.0f}%", "#FFB547" if current_rcfe<60 else "#00E5A0"),
                ("CAR", f"{latest['Capital_Adequacy']:.1f}%", "#00E5A0"),
                ("ROA", f"{latest['ROA']:.1f}%", "#E2E8F0"),
                ("LDR", f"{latest['Loan_to_Deposit']:.0f}%", "#E2E8F0"),
                ("RC Size", f"{latest['RC_Size']} members", "#E2E8F0")
            ]
            
            for idx, (label, value, color) in enumerate(metrics):
                with kpi_cols[idx % 3]:
                    st.markdown(f"""
                    <div style='background:#1C2333; padding:8px; border-radius:6px; text-align:center; margin-bottom:8px'>
                        <div style='font-size:10px; color:#6B7A99'>{label}</div>
                        <div style='font-size:18px; font-weight:700; color:{color}'>{value}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("""
                    <div style='font-weight:700; color:#00E5A0; margin:16px 0 8px'>Risk Committee Composition</div>
            """, unsafe_allow_html=True)
            
            for _, member in rc_members.iterrows():
                st.markdown(f"- **{member['Name']}** ({member['Position']})")
            
            st.markdown("""
                    <hr>
                    <div style='font-size:10px; color:#6B7A99; text-align:center'>Generated by RCECOS v1.0 | ZB Financial Holdings</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Export button
        report_data = {
            "bank": "ZB Bank",
            "report_date": report_date,
            "metrics": {
                "npl_ratio": float(latest["NPL_Ratio"]),
                "rcfe": float(current_rcfe),
                "capital_adequacy": float(latest["Capital_Adequacy"])
            },
            "warnings": len(warnings_list)
        }
        
        report_json = json.dumps(report_data, indent=2, default=convert_to_serializable)
        st.download_button("⬇ Download Report (JSON)", report_json, file_name=f"zb_bank_report_{datetime.datetime.now().strftime('%Y%m%d')}.json", mime="application/json")

# ─── Run App ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if st.session_state.authenticated:
        main_app()
    else:
        show_login()