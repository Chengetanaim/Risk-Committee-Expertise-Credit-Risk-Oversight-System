import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import hashlib
import re
import json
import warnings
warnings.filterwarnings('ignore')

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ZB Bank | RCECOS - Risk Committee Oversight System",
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
if "loan_scanner_history" not in st.session_state:
    st.session_state.loan_scanner_history = []
if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = None
if "corrective_actions" not in st.session_state:
    st.session_state.corrective_actions = []

# ─── Helper function for JSON serialization ──────────────────────────────────
def convert_to_serializable(obj):
    if isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj

# ─── ZB BANK DATA (Pre-ingested - Real data from the Excel) ───────────────────
def load_zb_bank_data():
    data = {
        "Year": [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
        "RCFE": [43, 43, 43, 50, 50, 50, 50, 50, 57, 57, 57, 57],
        "NPL_Ratio": [19.5, 18.9, 17.4, 9.5, 12, 12, 6.8, 6.2, 5.4, 4.5, 3.5, 3.9],
        "Capital_Adequacy": [16.2, 15.8, 15.5, 16, 16.5, 17, 18.5, 20, 22, 24, 26, 27.5],
        "ROA": [1.2, 1.0, 0.8, 0.7, 1.0, 1.2, 1.0, 1.1, 1.8, 2.5, 2.8, 2.6],
        "Loan_to_Deposit": [58, 59, 57, 55, 56, 57, 53, 50, 47, 44, 42, 40],
        "Loan_Portfolio_Billion": [0.85, 0.88, 0.82, 0.78, 0.81, 0.86, 0.92, 1.02, 1.15, 1.28, 1.35, 1.42],
        "Overdue_Facilities_pct": [8.5, 8.2, 7.8, 4.2, 5.5, 5.5, 3.2, 2.9, 2.5, 2.1, 1.6, 1.8],
        "Provisioning_Coverage": [62, 60, 58, 65, 68, 70, 72, 75, 78, 80, 82, 85]
    }
    return pd.DataFrame(data)

def get_risk_committee_members():
    members = pd.DataFrame({
        "Name": ["Prof. Tafadzwa Ncube", "Mr. Charles Mutasa", "Mrs. Grace Mapondera", "Dr. Tendai Makoni"],
        "Position": ["Chairperson", "Member", "Independent Member", "Observer"],
        "Qualifications": ["PhD Finance, CFA, MBA", "CFA, ACCA, MSc Banking", "CA(Z), MSc Finance, FRM", "PhD Economics, MSc RM"],
        "Expertise_Score": [95, 82, 90, 78],
        "Experience_Years": [18, 14, 20, 12],
        "Risk_Management_Certified": [True, True, True, False],
        "Board_Director_Experience": [True, False, True, False]
    })
    return members

# ─── LOAN RISK SCANNER FUNCTIONS ──────────────────────────────────────────────
def calculate_loan_risk_score(loan_data):
    score = 0
    risk_factors = []
    
    dti = loan_data.get("dti", 0)
    if dti > 0.5:
        score += 30
        risk_factors.append("High debt-to-income ratio (>50%)")
    elif dti > 0.35:
        score += 15
        risk_factors.append("Moderate DTI (>35%)")
    
    repayment = loan_data.get("repayment_history", "good")
    if repayment == "poor":
        score += 40
        risk_factors.append("Poor repayment history - multiple defaults")
    elif repayment == "fair":
        score += 20
        risk_factors.append("Fair repayment history - occasional late payments")
    
    sector = loan_data.get("sector", "unknown")
    sector_risk = {"agriculture": 35, "mining": 30, "manufacturing": 25, "retail": 15, "services": 10}
    score += sector_risk.get(sector.lower(), 20)
    risk_factors.append(f"Sector: {sector}")
    
    collateral = loan_data.get("collateral", 0)
    if collateral < 0.5:
        score += 25
        risk_factors.append("Low collateral coverage (<50%)")
    
    relationship = loan_data.get("relationship_years", 3)
    if relationship < 1:
        score += 15
        risk_factors.append("New customer (<1 year)")
    
    final_score = min(score, 100)
    
    if final_score >= 70:
        category = "Critical"
        action = "Immediate committee review - DO NOT APPROVE"
        icon = "🔴"
        color = "#FF4D6A"
    elif final_score >= 45:
        category = "Elevated"
        action = "Enhanced due diligence required. Committee member sign-off needed"
        icon = "🟠"
        color = "#FFB547"
    elif final_score >= 20:
        category = "Moderate"
        action = "Standard review with committee notification"
        icon = "🟡"
        color = "#0091FF"
    else:
        category = "Low"
        action = "Fast-track approval"
        icon = "🟢"
        color = "#00E5A0"
    
    return {"score": final_score, "category": category, "action": action, "icon": icon, "color": color, "factors": risk_factors}

# ─── RCFE SIMULATOR FUNCTIONS ─────────────────────────────────────────────────
def run_rcfe_simulation(current_rcfe, current_npl, target_rcfe):
    rcfe_improvement = (target_rcfe - current_rcfe) / 100
    expected_npl_reduction_pct = rcfe_improvement * 0.75 * 100
    expected_new_npl = current_npl * (1 - expected_npl_reduction_pct / 100)
    
    if rcfe_improvement > 0.2:
        timeline = "6-12 months (committee restructuring + training)"
    elif rcfe_improvement > 0.1:
        timeline = "3-6 months (targeted recruitment + CPD)"
    else:
        timeline = "1-3 months (minor adjustments)"
    
    loan_portfolio = 1000
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

# ─── Authentication Functions with Validation ─────────────────────────────────
def validate_username(username):
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be 3-20 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscore"
    return True, ""

def validate_password(password):
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(username, password):
    if username in st.session_state.users:
        return st.session_state.users[username] == hash_password(password)
    return False

def register_user(username, password):
    if username in st.session_state.users:
        return False, "Username already exists"
    valid, msg = validate_username(username)
    if not valid:
        return False, msg
    valid, msg = validate_password(password)
    if not valid:
        return False, msg
    st.session_state.users[username] = hash_password(password)
    return True, "Registration successful"

# ─── Helper Functions for Reports ────────────────────────────────────────────
def risk_badge(npl):
    if npl >= 10: return "🔴 CRITICAL"
    elif npl >= 7: return "🟠 ELEVATED"
    elif npl >= 4: return "🟡 MODERATE"
    else: return "🟢 ACCEPTABLE"

def expertise_badge(score):
    if score >= 75: return "🟢 HIGH"
    elif score >= 50: return "🟡 MODERATE"
    else: return "🔴 LOW"

def generate_early_warnings(df, committee, thresholds):
    """Generate alerts based on current data"""
    latest = df.iloc[-1]
    avg_exp = committee["Expertise_Score"].mean()
    alerts = []
    
    if latest["NPL_Ratio"] >= thresholds["npl_crit"]:
        alerts.append({"Severity": "🔴 CRITICAL", "Indicator": "NPL Ratio",
                       "Value": f"{latest['NPL_Ratio']:.1f}%", "Threshold": f"{thresholds['npl_crit']}%",
                       "Action": "Immediate board review + provisioning increase"})
    elif latest["NPL_Ratio"] >= thresholds["npl_warn"]:
        alerts.append({"Severity": "🟠 WARNING", "Indicator": "NPL Ratio",
                       "Value": f"{latest['NPL_Ratio']:.1f}%", "Threshold": f"{thresholds['npl_warn']}%",
                       "Action": "Enhanced monitoring + credit committee review"})
    
    if latest["Overdue_Facilities_pct"] >= thresholds["overdue"]:
        alerts.append({"Severity": "🟡 CAUTION", "Indicator": "Overdue Facilities",
                       "Value": f"{latest['Overdue_Facilities_pct']:.1f}%", "Threshold": f"{thresholds['overdue']}%",
                       "Action": "Review collections strategy"})
    
    if latest["Provisioning_Coverage"] < thresholds["provision"]:
        alerts.append({"Severity": "🟡 CAUTION", "Indicator": "Provisioning Coverage",
                       "Value": f"{latest['Provisioning_Coverage']:.1f}%", "Threshold": f"< {thresholds['provision']}%",
                       "Action": "Increase loan loss reserves"})
    
    if avg_exp < thresholds["expertise"]:
        alerts.append({"Severity": "🟠 WARNING", "Indicator": "Committee Expertise",
                       "Value": f"{avg_exp:.0f}/100", "Threshold": f"< {thresholds['expertise']}",
                       "Action": "Board appointment review — recruit financial expert"})
    
    if latest["Capital_Adequacy"] < thresholds["capital"]:
        alerts.append({"Severity": "🔴 CRITICAL", "Indicator": "Capital Adequacy",
                       "Value": f"{latest['Capital_Adequacy']:.1f}%", "Threshold": f"< {thresholds['capital']}%",
                       "Action": "Urgent capital plan — notify RBZ"})
    
    return alerts

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
.section-header { font-family: 'Barlow Condensed', sans-serif; font-size: 18px; font-weight: 700; border-left: 3px solid #00E5A0; padding-left: 12px; margin: 20px 0 16px; text-transform: uppercase; }
.card { background: #1C2333; border: 1px solid #2A3347; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.member-card { background: #111827; border: 1px solid #2A3347; border-radius: 8px; padding: 12px; margin: 8px 0; }
</style>
""", unsafe_allow_html=True)

# ─── Login UI ─────────────────────────────────────────────────────────────────
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center;margin-bottom:32px'>
            <div style='font-size:48px;font-weight:700;color:#00E5A0'>ZB Bank</div>
            <div style='font-size:14px;color:#6B7A99'>Risk Committee Expertise & Credit Risk Oversight System</div>
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
                new_username = st.text_input("Username (3-20 chars, letters/numbers/underscore)")
                new_password = st.text_input("Password (min 6 characters)", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("Sign Up", use_container_width=True):
                    if not new_username or not new_password:
                        st.error("Please fill all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, msg = register_user(new_username, new_password)
                        if success:
                            st.success(msg + "! Please sign in.")
                        else:
                            st.error(msg)

# ─── Main Application ─────────────────────────────────────────────────────────
def main_app():
    df = load_zb_bank_data()
    committee = get_risk_committee_members()
    latest = df.iloc[-1]
    
    # Default thresholds
    thresholds = {
        "npl_warn": 7.0,
        "npl_crit": 10.0,
        "overdue": 6.0,
        "provision": 50.0,
        "expertise": 60,
        "capital": 12.0
    }
    
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:16px 0 8px'>
            <div style='font-size:10px;color:#6B7A99'>Signed in as</div>
            <div style='font-size:18px;font-weight:700;color:#00E5A0'>{st.session_state.username}</div>
            <div style='font-size:11px;color:#6B7A99'>ZB Bank • Risk Oversight</div>
        </div>
        <hr>
        """, unsafe_allow_html=True)
        
        st.markdown("### 🎯 Navigation")
        page = st.radio("", [
            "🏆 1. Risk Committee Expertise",
            "📊 2. Credit Risk (Loan Risk Indicator)",
            "📈 3. RCFE vs NPL Relationship",
            "💰 4. Loan Portfolio Ratio",
            "🚨 5. Early Warning Indicator",
            "📋 6. Report (Corrective Actions)"
        ], label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()
    
    # Header
    st.markdown("""
    <div style='margin-bottom:16px'>
        <div style='font-size:10px;color:#6B7A99;font-family:"IBM Plex Mono"'>ZB FINANCIAL HOLDINGS</div>
        <div style='font-size:28px;font-weight:700;font-family:"Barlow Condensed"'>Risk Committee Oversight System</div>
        <div style='font-size:13px;color:#6B7A99'>Chapter 4 Implementation | Prioritized Dashboard</div>
    </div>
    """, unsafe_allow_html=True)
    
    # ──────────────────────────────────────────────────────────────────────────
    # PRIORITY 1: RISK COMMITTEE EXPERTISE
    # ──────────────────────────────────────────────────────────────────────────
    if page == "🏆 1. Risk Committee Expertise":
        st.markdown('<div class="section-header">🏆 Risk Committee Financial Expertise</div>', unsafe_allow_html=True)
        
        current_rcfe = latest["RCFE"]
        target_rcfe = 60
        gap = target_rcfe - current_rcfe
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current RCFE", f"{current_rcfe}%", delta=f"Target: {target_rcfe}%", delta_color="inverse")
        with col2:
            st.metric("RCFE Gap to Target", f"+{gap}%", delta="Need to close", delta_color="inverse")
        with col3:
            avg_expertise = committee["Expertise_Score"].mean()
            st.metric("Avg Member Expertise", f"{avg_expertise:.0f}/100", delta="Committee quality")
        
        st.markdown("### 📋 Current Risk Committee Members")
        st.dataframe(committee, use_container_width=True, hide_index=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Year"], y=df["RCFE"], mode="lines+markers", name="RCFE %", line=dict(color="#00E5A0", width=3), marker=dict(size=10)))
        fig.add_hline(y=60, line_dash="dash", line_color="#00E5A0", annotation_text="Target 60%")
        fig.add_hline(y=50, line_dash="dash", line_color="#FFB547", annotation_text="Minimum 50%")
        fig.update_layout(title="Risk Committee Financial Expertise Trend (2013-2024)", height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
        if current_rcfe < 60:
            st.warning(f"⚠️ Current RCFE is {current_rcfe}%, below target of 60%. Recommended actions:")
            st.markdown("""
            1. **Recruit additional CFA/FRM certified member** to risk committee within 90 days
            2. **Implement quarterly training program** on IFRS 9 and Basel III
            3. **Annual skills assessment** to identify and address expertise gaps
            """)
        else:
            st.success("✅ RCFE meets target. Maintain through continuous professional development.")
    
    # ──────────────────────────────────────────────────────────────────────────
    # PRIORITY 2: CREDIT RISK (Loan Risk Indicator)
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "📊 2. Credit Risk (Loan Risk Indicator)":
        st.markdown('<div class="section-header">📊 Credit Risk - Loan Risk Indicator</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background:#111827; padding:12px; border-radius:8px; margin-bottom:16px'>
            <div style='font-size:13px; color:#B0BAD0'>Assess individual loan applications. The system calculates a risk score based on borrower characteristics and recommends committee action.</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📝 Loan Application Details")
            loan_amount = st.number_input("Loan Amount (ZW$)", min_value=1000, max_value=50000000, value=500000, step=10000)
            monthly_income = st.number_input("Monthly Income (ZW$)", min_value=1000, max_value=5000000, value=50000, step=5000)
            dti = (loan_amount / 12) / monthly_income if monthly_income > 0 else 0
            st.caption(f"Debt-to-Income: {dti:.2f} {'⚠️ High' if dti > 0.5 else '✅ OK'}")
            
            sector = st.selectbox("Economic Sector", ["Agriculture", "Mining", "Manufacturing", "Retail", "Services"])
            repayment_history = st.selectbox("Repayment History", ["Good", "Fair", "Poor"])
            collateral = st.slider("Collateral Coverage (%)", 0, 150, 70) / 100
            relationship_years = st.number_input("Years with Bank", min_value=0, max_value=20, value=3)
            
        with col2:
            st.markdown("### 🏦 Bank Context")
            st.metric("Current Bank RCFE", f"{latest['RCFE']}%", delta="Affects approval threshold")
            st.metric("Current Bank NPL", f"{latest['NPL_Ratio']}%", delta="Sector average")
            
            if st.button("🔍 CALCULATE LOAN RISK", use_container_width=True):
                risk = calculate_loan_risk_score({
                    "dti": dti, "repayment_history": repayment_history.lower(),
                    "sector": sector.lower(), "collateral": collateral,
                    "relationship_years": relationship_years
                })
                
                st.markdown(f"""
                <div class='card' style='margin-top:20px; border-left: 4px solid {risk["color"]}'>
                    <div style='text-align:center'>
                        <div style='font-size:48px; font-weight:700'>{risk["icon"]} {risk["score"]}/100</div>
                        <div style='font-size:18px; font-weight:700; color:{risk["color"]}'>{risk["category"]} RISK</div>
                    </div>
                    <hr>
                    <div><b>Recommended Action:</b> {risk["action"]}</div>
                    <div style='margin-top:8px'><b>Risk Factors:</b></div>
                """, unsafe_allow_html=True)
                for factor in risk["factors"]:
                    st.markdown(f"- {factor}")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.session_state.loan_scanner_history.append({
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "amount": loan_amount, "sector": sector, "risk_score": risk["score"], "category": risk["category"]
                })
        
        if st.session_state.loan_scanner_history:
            st.markdown("### 📋 Recent Loan Assessments")
            history_df = pd.DataFrame(st.session_state.loan_scanner_history[-5:])
            st.dataframe(history_df, use_container_width=True)
    
    # ──────────────────────────────────────────────────────────────────────────
    # PRIORITY 3: RCFE vs NPL RELATIONSHIP (Year Comparison)
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "📈 3. RCFE vs NPL Relationship":
        st.markdown('<div class="section-header">📈 RCFE vs NPL Relationship Analysis</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style='background:#111827; padding:12px; border-radius:8px; margin-bottom:16px'>
            <div style='font-size:13px; color:#B0BAD0'>Select any two years to compare how changes in Risk Committee Financial Expertise (RCFE) affected Non-Performing Loan (NPL) ratios.</div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            year1 = st.selectbox("Base Year", df["Year"].tolist(), index=0)
        with col2:
            year2 = st.selectbox("Comparison Year", df["Year"].tolist(), index=11)
        
        data1 = df[df["Year"] == year1].iloc[0]
        data2 = df[df["Year"] == year2].iloc[0]
        
        rcfe_change = data2["RCFE"] - data1["RCFE"]
        npl_change = data2["NPL_Ratio"] - data1["NPL_Ratio"]
        
        st.markdown(f"""
        <div class='card'>
            <div style='display:grid; grid-template-columns:1fr auto 1fr; gap:16px; text-align:center'>
                <div>
                    <div style='font-size:12px; color:#6B7A99'>{year1}</div>
                    <div style='font-size:28px; font-weight:700'>RCFE: {data1['RCFE']}%</div>
                    <div style='font-size:24px'>NPL: {data1['NPL_Ratio']}%</div>
                </div>
                <div style='font-size:24px; align-self:center'>→</div>
                <div>
                    <div style='font-size:12px; color:#6B7A99'>{year2}</div>
                    <div style='font-size:28px; font-weight:700'>RCFE: {data2['RCFE']}%</div>
                    <div style='font-size:24px'>NPL: {data2['NPL_Ratio']}%</div>
                </div>
            </div>
            <hr>
            <div style='text-align:center'>
                <div style='font-size:16px'>RCFE Change: <b style='color:{"#00E5A0" if rcfe_change > 0 else "#FF4D6A"}'>{'+' if rcfe_change > 0 else ''}{rcfe_change}%</b></div>
                <div style='font-size:16px'>NPL Change: <b style='color:{"#00E5A0" if npl_change < 0 else "#FF4D6A"}'>{'+' if npl_change > 0 else ''}{npl_change}%</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Full trend visualization with dual axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df["Year"], y=df["RCFE"], name="RCFE (%)", line=dict(color="#00E5A0", width=3)), secondary_y=False)
        fig.add_trace(go.Scatter(x=df["Year"], y=df["NPL_Ratio"], name="NPL Ratio (%)", line=dict(color="#FF4D6A", width=3)), secondary_y=True)
        fig.update_layout(title="RCFE vs NPL Ratio Over Time (2013-2024)", height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(title_text="RCFE (%)", color="#00E5A0", secondary_y=False)
        fig.update_yaxes(title_text="NPL (%)", color="#FF4D6A", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # Correlation and finding
        corr = df["RCFE"].corr(df["NPL_Ratio"])
        
        st.markdown(f"""
        <div class='card' style='background:rgba(0,229,160,0.05); border-color:#00E5A0'>
            <div style='font-weight:700; color:#00E5A0'>📊 Statistical Finding</div>
            <div style='font-size:14px; margin-top:8px'>
                <b>Pearson Correlation (2013-2024): r = {corr:.3f}</b><br>
                This {'negative' if corr < 0 else 'positive'} correlation indicates that 
                {'as RCFE increases, NPL decreases - supporting H₁' if corr < 0 else 'the relationship requires further analysis'}.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # ──────────────────────────────────────────────────────────────────────────
    # PRIORITY 4: LOAN PORTFOLIO RATIO
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "💰 4. Loan Portfolio Ratio":
        st.markdown('<div class="section-header">💰 Loan Portfolio Analysis</div>', unsafe_allow_html=True)
        
        npl_amount = latest["Loan_Portfolio_Billion"] * (latest["NPL_Ratio"] / 100)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Loan Portfolio", f"ZW${latest['Loan_Portfolio_Billion']:.2f}B", delta=f"From ZW${df.iloc[0]['Loan_Portfolio_Billion']:.2f}B in 2013")
        with col2:
            st.metric("NPL Amount", f"ZW${npl_amount:.2f}B", delta=f"{latest['NPL_Ratio']}% of portfolio", delta_color="inverse")
        with col3:
            st.metric("Loan-to-Deposit Ratio", f"{latest['Loan_to_Deposit']:.0f}%", delta="Liquidity indicator")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["Year"], y=df["Loan_Portfolio_Billion"], name="Loan Portfolio (ZW$B)", marker_color="#0091FF"))
        fig.add_trace(go.Scatter(x=df["Year"], y=df["NPL_Ratio"], name="NPL Ratio (%)", line=dict(color="#FF4D6A", width=3), yaxis="y2"))
        fig.update_layout(title="Loan Portfolio Growth vs NPL Ratio", height=450, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_yaxes(title_text="Loan Portfolio (ZW$ Billion)", color="#0091FF")
        fig.update_yaxes(title_text="NPL Ratio (%)", color="#FF4D6A", overlaying="y", side="right")
        st.plotly_chart(fig, use_container_width=True)
    
    # ──────────────────────────────────────────────────────────────────────────
    # PRIORITY 5: EARLY WARNING INDICATOR
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "🚨 5. Early Warning Indicator":
        st.markdown('<div class="section-header">🚨 Early Warning Indicator System</div>', unsafe_allow_html=True)
        
        def calculate_ews(npl, rcfe, car, roa):
            score = 0
            if npl > 7: score += 40
            elif npl > 5: score += 20
            if rcfe < 50: score += 30
            elif rcfe < 60: score += 15
            if car < 12: score += 20
            elif car < 15: score += 10
            if roa < 1: score += 10
            
            if score >= 60: level, color = "🔴 CRITICAL", "#FF4D6A"
            elif score >= 35: level, color = "🟠 ELEVATED", "#FFB547"
            elif score >= 15: level, color = "🟡 MODERATE", "#0091FF"
            else: level, color = "🟢 LOW", "#00E5A0"
            return {"score": score, "level": level, "color": color}
        
        ews = calculate_ews(latest["NPL_Ratio"], latest["RCFE"], latest["Capital_Adequacy"], latest["ROA"])
        
        st.markdown(f"""
        <div class='card' style='text-align:center; border-left: 4px solid {ews["color"]}'>
            <div style='font-size:14px; color:#6B7A99'>CURRENT EARLY WARNING STATUS</div>
            <div style='font-size:48px; font-weight:700; color:{ews["color"]}'>{ews["level"]}</div>
            <div style='font-size:16px'>Overall Risk Score: {ews["score"]}/100</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Component breakdown
        st.markdown("### 📊 EWS Component Breakdown")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            npl_score = 40 if latest["NPL_Ratio"] > 7 else 20 if latest["NPL_Ratio"] > 5 else 0
            st.metric("NPL Component", f"{npl_score}/40", delta=f"NPL: {latest['NPL_Ratio']}%")
        with col2:
            rcfe_score = 30 if latest["RCFE"] < 50 else 15 if latest["RCFE"] < 60 else 0
            st.metric("RCFE Component", f"{rcfe_score}/30", delta=f"RCFE: {latest['RCFE']}%")
        with col3:
            car_score = 20 if latest["Capital_Adequacy"] < 12 else 10 if latest["Capital_Adequacy"] < 15 else 0
            st.metric("Capital Component", f"{car_score}/20", delta=f"CAR: {latest['Capital_Adequacy']}%")
        with col4:
            roa_score = 10 if latest["ROA"] < 1 else 0
            st.metric("ROA Component", f"{roa_score}/10", delta=f"ROA: {latest['ROA']}%")
        
        # EWS Trend
        df["EWS_Score"] = df.apply(lambda row: calculate_ews(row["NPL_Ratio"], row["RCFE"], row["Capital_Adequacy"], row["ROA"])["score"], axis=1)
        fig = px.area(df, x="Year", y="EWS_Score", title="Early Warning System Trend (Lower is Better)", color_discrete_sequence=["#00E5A0"])
        fig.add_hline(y=60, line_dash="dash", line_color="#FF4D6A", annotation_text="Critical Zone")
        fig.add_hline(y=35, line_dash="dash", line_color="#FFB547", annotation_text="Elevated Zone")
        fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    
    # ──────────────────────────────────────────────────────────────────────────
    # PRIORITY 6: REPORT (Corrective Actions) - WITH FULL REPORTING
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "📋 6. Report (Corrective Actions)":
        st.markdown('<div class="section-header">📋 Board Risk Committee Reports & Corrective Actions</div>', unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════════
        # REPORT CONTROLS — bank + period selectors (from commit 42b745a)
        # ══════════════════════════════════════════════════════════════════
        REPORT_BANKS = ["ZB Bank", "CBZ Bank", "Steward Bank", "NMB Bank", "BancABC", "Ecobank Zimbabwe", "FBC Bank"]
        REPORT_YEARS = list(range(2013, 2025))

        # Synthetic per-bank data for reporting (expertise drives outcomes)
        _BANK_PROFILES = {
            "ZB Bank":            (72, 3.9,  1.8,  85, 27.5, 1.8, 40),
            "CBZ Bank":           (78, 2.8,  2.1,  88, 29.0, 1.5, 38),
            "Steward Bank":       (65, 6.1,  1.1,  70, 18.5, 2.8, 55),
            "NMB Bank":           (60, 7.4,  0.9,  62, 15.2, 3.2, 60),
            "BancABC":            (52, 9.2,  0.7,  57, 13.4, 4.1, 68),
            "Ecobank Zimbabwe":   (45, 11.0, 0.5,  51, 12.1, 5.5, 74),
            "FBC Bank":           (40, 12.8, 0.3,  44, 11.5, 6.8, 80),
        }
        _BANK_MEMBERS = {
            "ZB Bank":           [("Prof. Tafadzwa Ncube","Chairperson","PhD Finance, CFA, MBA",95,True,True),
                                   ("Mr. Charles Mutasa","Member","CFA, ACCA, MSc Banking",82,True,False),
                                   ("Mrs. Grace Mapondera","Independent Member","CA(Z), MSc Finance, FRM",90,True,True),
                                   ("Dr. Tendai Makoni","Observer","PhD Economics, MSc RM",78,False,False)],
            "CBZ Bank":          [("Dr. Faith Chikwanda","Chairperson","PhD Finance, CFA",92,True,True),
                                   ("Mr. Tawanda Moyo","Member","CFA, MSc Banking",85,True,True),
                                   ("Ms. Rudo Sibanda","Independent Member","CA(Z), FRM",88,True,True)],
            "Steward Bank":      [("Dr. John Muza","Chairperson","PhD Finance",75,True,True),
                                   ("Ms. Tsitsi Hlupeko","Member","MBA Finance, ACCA",62,True,False)],
            "NMB Bank":          [("Mr. Simba Kurasha","Chairperson","MBA Finance",58,False,True),
                                   ("Dr. Nyarai Banda","Member","MSc Banking, CPA",63,True,False)],
            "BancABC":           [("Mrs. Anesu Chigumira","Chairperson","MBA Finance",50,False,False),
                                   ("Mr. Kudakwashe Dube","Member","ACCA",48,False,True)],
            "Ecobank Zimbabwe":  [("Prof. Munyaradzi Juru","Chairperson","MBA Finance",46,False,False),
                                   ("Ms. Tatenda Gwanetsa","Member","CPA",44,False,False)],
            "FBC Bank":          [("Dr. Farai Makwara","Chairperson","MSc Banking",42,False,False),
                                   ("Mr. Paidamoyo Zvimba","Member","CPA",38,False,False)],
        }

        rcol1, rcol2 = st.columns([2, 2])
        with rcol1:
            r_bank = st.selectbox("🏦 Bank for Report", REPORT_BANKS, key="r_bank")
        with rcol2:
            r_period = st.selectbox("📅 Reporting Period", [str(y) for y in reversed(REPORT_YEARS)], key="r_period")

        # Build report data for selected bank/period
        bp = _BANK_PROFILES[r_bank]
        r_avg_exp, r_npl, r_roa, r_prov, r_cap, r_overdue, r_ldr = bp
        # Apply small year-based variance
        yr_offset = (int(r_period) - 2024) * 0.15
        r_npl  = max(1.0, round(r_npl  + yr_offset, 1))
        r_cap  = max(8.0, round(r_cap  - yr_offset * 0.5, 1))
        r_prov = max(30,  round(r_prov - yr_offset * 2, 0))

        r_members_raw = _BANK_MEMBERS[r_bank]
        r_comm = pd.DataFrame(r_members_raw, columns=["Name","Role","Qualifications","Expertise_Score","Risk_Management_Certified","Board_Director_Experience"])
        r_avg_exp_actual = r_comm["Expertise_Score"].mean()

        st.markdown("---")

        # ==================== SECTION A: EARLY WARNING ALERTS ====================
        st.markdown("### 🚨 Early Warning Alerts")

        alerts = generate_early_warnings(df, committee, thresholds)

        if alerts:
            alert_df = pd.DataFrame(alerts)
            col1, col2, col3 = st.columns(3)
            n_crit = sum(1 for a in alerts if "CRITICAL" in a["Severity"])
            n_warn = sum(1 for a in alerts if "WARNING" in a["Severity"])
            n_caut = sum(1 for a in alerts if "CAUTION" in a["Severity"])
            col1.metric("🔴 Critical Alerts", str(n_crit))
            col2.metric("🟠 Warnings", str(n_warn))
            col3.metric("🟡 Cautions", str(n_caut))
            st.dataframe(alert_df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No active alerts under current thresholds.")

        # ==================== SECTION B: ADD CORRECTIVE ACTION ====================
        with st.expander("➕ Register New Corrective Action", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                action_title = st.text_input("Action Title")
                assigned_to = st.selectbox("Assigned To", committee["Name"].tolist() + ["Risk Committee", "Management", "External Audit"])
                deadline = st.date_input("Deadline", datetime.date.today() + datetime.timedelta(days=30))
                priority = st.selectbox("Priority", ["Critical", "High", "Medium", "Low"])
            with col2:
                risk_area = st.selectbox("Risk Area", ["RCFE Improvement", "NPL Reduction", "Capital Adequacy", "Loan Underwriting", "Early Warning System", "Portfolio Diversification"])
                status = st.selectbox("Status", ["Not Started", "In Progress", "Under Review", "Completed"])
                linked_alert = st.selectbox("Linked Alert (if any)", ["None"] + [a["Indicator"] for a in alerts]) if alerts else "None"

            description = st.text_area("Action Description", height=100)

            if st.button("📌 Register Corrective Action", use_container_width=True):
                st.session_state.corrective_actions.append({
                    "id": len(st.session_state.corrective_actions) + 1,
                    "title": action_title, "risk_area": risk_area, "assigned_to": assigned_to,
                    "deadline": deadline.strftime("%Y-%m-%d"), "priority": priority,
                    "status": status, "description": description, "linked_alert": linked_alert,
                    "created": datetime.datetime.now().strftime("%Y-%m-%d")
                })
                st.success("Action registered successfully!")
                st.rerun()

        # ==================== SECTION C: CORRECTIVE ACTIONS TRACKER ====================
        if st.session_state.corrective_actions:
            st.markdown("### 📋 Corrective Actions Tracker")
            actions_df = pd.DataFrame(st.session_state.corrective_actions)

            def priority_icon(p):
                return "🔴" if p == "Critical" else "🟠" if p == "High" else "🟡" if p == "Medium" else "🟢"

            actions_df["Prio"] = actions_df["priority"].apply(priority_icon)
            st.dataframe(actions_df[["Prio", "title", "risk_area", "assigned_to", "deadline", "status"]], use_container_width=True)

            col_a, col_b, col_c, col_d = st.columns(4)
            total_actions = len(actions_df)
            completed = len(actions_df[actions_df["status"] == "Completed"])
            in_progress = len(actions_df[actions_df["status"] == "In Progress"])
            overdue = len(actions_df[(actions_df["deadline"] < datetime.date.today().strftime("%Y-%m-%d")) & (actions_df["status"] != "Completed")])

            col_a.metric("Total Actions", total_actions)
            col_b.metric("Completed", completed, delta=f"{completed/total_actions*100:.0f}%" if total_actions > 0 else "0%")
            col_c.metric("In Progress", in_progress)
            col_d.metric("Overdue", overdue, delta="⚠️ Review required" if overdue > 0 else None, delta_color="inverse")

        # ==================== SECTION D: BOARD RISK COMMITTEE REPORT ====================
        st.markdown("### 📄 Board Risk Committee Report")

        report_date = datetime.datetime.now().strftime("%d %B %Y")

        npl_color  = "#FF4D6A" if r_npl  >= thresholds["npl_warn"]  else "#00E5A0"
        cap_color  = "#FF4D6A" if r_cap  < 12                        else "#00E5A0"
        rcfe_color = "#FFB547" if r_avg_exp_actual < 60               else "#00E5A0"

        st.markdown(f"""
        <div style='background:#111827;border:1px solid #2A3347;border-radius:8px;padding:28px 32px;margin:16px 0'>
          <div style='font-family:"IBM Plex Mono",monospace;font-size:10px;color:#6B7A99;text-transform:uppercase;letter-spacing:.12em'>Confidential — Board Risk Committee Report</div>
          <div style='font-family:"Barlow Condensed",sans-serif;font-size:28px;font-weight:700;margin:8px 0 4px'>CREDIT RISK OVERSIGHT REPORT</div>
          <div style='font-family:"IBM Plex Mono",monospace;font-size:12px;color:#00E5A0'>{r_bank} &nbsp;|&nbsp; Period: {r_period} &nbsp;|&nbsp; Generated: {report_date}</div>
          <hr style='border-color:#2A3347;margin:20px 0'>

          <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;color:#E2E8F0'>1. Executive Summary</div>
          <div style='font-family:"Barlow",sans-serif;font-size:14px;color:#B0BAD0;line-height:1.7;margin-bottom:20px'>
          As at <b>{r_period}</b>, {r_bank} recorded a Non-Performing Loan (NPL) ratio of
          <span style='color:{npl_color}'><b>{r_npl:.1f}%</b></span>
          against a monitoring threshold of {thresholds["npl_warn"]}%. The bank's provisioning coverage stood at
          <b>{r_prov:.0f}%</b> and capital adequacy at <b>{r_cap:.1f}%</b>.
          The risk committee's average financial expertise score is <b>{r_avg_exp_actual:.0f}/100</b>
          ({expertise_badge(r_avg_exp_actual)}).
          </div>

          <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;color:#E2E8F0'>2. Key Credit Risk Indicators</div>
          <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px'>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>NPL Ratio</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:{npl_color}'>{r_npl:.1f}%</div>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:10px;color:#6B7A99'>{risk_badge(r_npl)}</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Overdue Facilities</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:#FFB547'>{r_overdue:.1f}%</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Provisioning Cover</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:#0091FF'>{r_prov:.0f}%</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Capital Adequacy</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:{cap_color}'>{r_cap:.1f}%</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Loan/Deposit Ratio</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:#A78BFA'>{r_ldr:.0f}%</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Return on Assets</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:#34D399'>{r_roa:.2f}%</div>
            </div>
          </div>

          <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;color:#E2E8F0'>3. Risk Committee Governance</div>
          <div style='font-family:"Barlow",sans-serif;font-size:14px;color:#B0BAD0;line-height:1.7;margin-bottom:16px'>
          The committee comprises <b>{len(r_comm)} members</b>.
          Average expertise score: <b>{r_avg_exp_actual:.0f}/100</b> ({expertise_badge(r_avg_exp_actual)}).
          Risk-certified members: <b>{r_comm["Risk_Management_Certified"].sum()}</b>.
          Board director experienced: <b>{r_comm["Board_Director_Experience"].sum()}</b>.
          </div>

          <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;color:#E2E8F0'>4. Corrective Actions Status</div>
          <div style='font-family:"Barlow",sans-serif;font-size:14px;color:#B0BAD0;line-height:1.7;margin-bottom:16px'>
            <b>Total Actions Registered:</b> {len(st.session_state.corrective_actions)}<br>
            <b>Completed:</b> {len([a for a in st.session_state.corrective_actions if a['status'] == 'Completed'])}<br>
            <b>In Progress:</b> {len([a for a in st.session_state.corrective_actions if a['status'] == 'In Progress'])}<br>
            <b>Overdue:</b> {len([a for a in st.session_state.corrective_actions if a['deadline'] < datetime.date.today().strftime("%Y-%m-%d") and a['status'] != 'Completed'])}
          </div>

          <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;color:#E2E8F0'>5. Recommendations</div>
          <div style='font-family:"Barlow",sans-serif;font-size:14px;color:#B0BAD0;line-height:1.7'>
          {"⚠ <b>Immediate action required:</b> NPL ratio exceeds the critical threshold. The board should convene an emergency credit risk review, mandate stress testing, and strengthen provisioning." if r_npl >= thresholds["npl_warn"] else "✅ Credit risk indicators are within acceptable bounds. The committee should maintain current monitoring frequency and review sector concentration limits at the next scheduled meeting."}
          {"<br>📌 <b>Governance:</b> Consider recruiting additional CFA/FRM-certified members to strengthen analytical depth of the committee." if r_avg_exp_actual < 60 else "<br>📌 <b>Governance:</b> Expertise composition is adequate — continue professional development programme."}
          {"<br>🏦 <b>Capital:</b> Capital adequacy is below the regulatory minimum of 12% — initiate a capital restoration plan and notify RBZ immediately." if r_cap < 12 else ""}
          </div>
          <hr style='border-color:#2A3347;margin:20px 0'>
          <div style='font-size:10px;color:#6B7A99;text-align:center'>Generated by RCECOS v2.0 | Zimbabwe Banking Sector Oversight</div>
        </div>
        """, unsafe_allow_html=True)

        # Committee members table for report
        st.markdown(f"**Committee Members — {r_bank}**")
        rep_comm = r_comm[["Name","Role","Qualifications","Expertise_Score"]].copy()
        rep_comm.columns = ["Name","Role","Qualifications","Score"]
        st.dataframe(rep_comm, use_container_width=True, hide_index=True)

        # ==================== SECTION E: GOVERNANCE ENHANCEMENT RECOMMENDATIONS ====================
        st.markdown('<div class="section-header">📐 Governance Enhancement Recommendations</div>', unsafe_allow_html=True)
        recs = [
            ("Mandatory Financial Expertise Threshold",
             "RBZ should mandate that at least 60% of risk committee members hold CFA, FRM, CA(Z) or equivalent qualifications. Banks falling below this threshold should be subject to enhanced supervisory review.",
             "Regulator / RBZ"),
            ("Structured Onboarding & Continuing Professional Development",
             "Banks should implement CPD programmes covering IFRS 9 expected credit loss, Basel III capital requirements and sector-specific credit analytics. Minimum 40 CPD hours per year for all committee members.",
             "Bank Boards"),
            ("Independent Risk Committee Chair",
             "The committee chair should be an independent non-executive director with minimum 10 years' senior banking experience and no executive relationship with management.",
             "Governance Committees"),
            ("Quarterly Credit Risk Reporting",
             "Boards should receive quarterly credit risk dashboards showing NPL trends, sector exposure heatmaps and provisioning adequacy, with automated early warning flags tied to RBZ thresholds.",
             "Risk Management"),
            ("ZAMCO Lessons Integration",
             "Governance frameworks should embed lessons from ZAMCO's NPL resolution, ensuring early identification of distressed assets before systemic accumulation. Mandatory stress testing twice annually.",
             "All Stakeholders"),
        ]
        for title, desc, owner in recs:
            st.markdown(f"""
            <div class='card'>
              <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;color:#E2E8F0'>{title}</div>
                <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#0091FF;text-transform:uppercase;letter-spacing:.08em;border:1px solid #0091FF;border-radius:3px;padding:2px 6px;white-space:nowrap;margin-left:12px'>{owner}</div>
              </div>
              <div style='font-family:"Barlow",sans-serif;font-size:13px;color:#8A98B8;margin-top:6px'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        # ==================== SECTION F: EXPORT REPORT ====================
        st.markdown("### 📎 Export Report")

        report_data = {
            "bank": r_bank,
            "report_date": report_date,
            "period": r_period,
            "metrics": {
                "npl_ratio": r_npl,
                "capital_adequacy": r_cap,
                "roa": r_roa,
                "loan_to_deposit_ratio": r_ldr,
                "overdue_facilities": r_overdue,
                "provisioning_coverage": r_prov,
            },
            "committee": {
                "avg_expertise": float(r_avg_exp_actual),
                "members": len(r_comm),
                "risk_certified": int(r_comm["Risk_Management_Certified"].sum())
            },
            "corrective_actions": {
                "total": len(st.session_state.corrective_actions),
                "completed": len([a for a in st.session_state.corrective_actions if a['status'] == 'Completed']),
                "in_progress": len([a for a in st.session_state.corrective_actions if a['status'] == 'In Progress'])
            },
            "alerts": len(alerts)
        }

        report_json = json.dumps(report_data, indent=2, default=convert_to_serializable)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("⬇ Download Report (JSON)", report_json,
                              file_name=f"{r_bank.replace(' ','_')}_report_{r_period}.json",
                              mime="application/json")
        with col2:
            csv_comm = r_comm.to_csv(index=False)
            st.download_button("⬇ Export Committee Data (CSV)", csv_comm,
                              file_name=f"{r_bank.replace(' ','_')}_committee_{r_period}.csv",
                              mime="text/csv")
        with col3:
            if st.session_state.corrective_actions:
                actions_df2 = pd.DataFrame(st.session_state.corrective_actions)
                csv_actions = actions_df2.to_csv(index=False)
                st.download_button("⬇ Export Corrective Actions (CSV)", csv_actions,
                                  file_name=f"corrective_actions_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                                  mime="text/csv")

# ─── Run App ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if st.session_state.authenticated:
        main_app()
    else:
        show_login()