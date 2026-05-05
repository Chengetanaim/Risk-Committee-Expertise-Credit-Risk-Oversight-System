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

# ─── Helper function for JSON serialization ──────────────────────────────────
def convert_to_serializable(obj):
    """Convert numpy/pandas types to Python native types for JSON serialization"""
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
    """Load ZB Bank's actual data from 2013-2024"""
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

# ─── Risk Committee Members Data for ZB Bank ──────────────────────────────────
def get_risk_committee_members():
    """Risk committee members with financial expertise levels"""
    members = pd.DataFrame({
        "Name": [
            "Prof. Tafadzwa Ncube",
            "Mr. Charles Mutasa", 
            "Mrs. Grace Mapondera",
            "Dr. Tendai Makoni"
        ],
        "Position": [
            "Chairperson - Risk Committee",
            "Member - Risk Committee",
            "Independent Member - Risk Committee",
            "Member - Risk Committee (Observer)"
        ],
        "Qualifications": [
            "PhD Finance, CFA, MBA",
            "CFA, ACCA, MSc Banking",
            "CA(Z), MSc Finance, FRM",
            "PhD Economics, MSc Risk Management"
        ],
        "Financial_Expertise_Level": [
            "Expert (15+ years)",
            "Advanced (12+ years)",
            "Expert (18+ years)",
            "Advanced (10+ years)"
        ],
        "Expertise_Score": [95, 82, 90, 78],
        "Independence": ["Independent", "Non-Independent", "Independent", "Independent"],
        "Risk_Experience_Years": [18, 14, 20, 12],
        "Certifications": ["CFA, FRM", "CFA, ACCA", "CA(Z), FRM", "PRM"]
    })
    return members

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

# ─── Chapter 4: Risk Committee Expertise Analysis ─────────────────────────────
def calculate_rcfe_score(df):
    """Calculate Risk Committee Financial Expertise score"""
    latest = df[df["Year"] == df["Year"].max()]
    rcfe = latest["RCFE"].values[0] if len(latest) > 0 else 0.5
    return rcfe * 100

def assess_rcfe_adequacy(rcfe_score):
    """Assess if RCFE is adequate based on Chapter 4 findings"""
    if rcfe_score >= 60:
        return "Adequate", "🟢", "Meets recommended threshold of 60%"
    elif rcfe_score >= 50:
        return "Moderate", "🟡", "Below recommended 60% threshold - improvement needed"
    else:
        return "Inadequate", "🔴", "Significantly below recommended threshold - urgent action required"

def get_rcfe_recommendations(rcfe_score, npl_ratio):
    """Generate specific recommendations based on RCFE and NPL"""
    recommendations = []
    
    if rcfe_score < 60:
        recommendations.append({
            "priority": "HIGH",
            "area": "Risk Committee Composition",
            "action": f"Current RCFE is {rcfe_score:.0f}%. Recruit at least 1 additional CFA/FRM certified member to reach 60% threshold.",
            "timeline": "Immediate (30 days)"
        })
        recommendations.append({
            "priority": "HIGH", 
            "area": "Member Qualifications",
            "action": "Require all risk committee members to complete IFRS 9 and Basel III training within 6 months.",
            "timeline": "6 months"
        })
    
    if npl_ratio > 7:
        recommendations.append({
            "priority": "CRITICAL",
            "area": "NPL Management",
            "action": f"NPL ratio at {npl_ratio:.1f}% exceeds 7% threshold. Convene emergency risk committee meeting.",
            "timeline": "Immediate (7 days)"
        })
        recommendations.append({
            "priority": "HIGH",
            "area": "Loan Review",
            "action": "Conduct special audit of all non-performing loans > ZW$1 million.",
            "timeline": "30 days"
        })
    
    if npl_ratio > 5 and rcfe_score < 60:
        recommendations.append({
            "priority": "MEDIUM",
            "area": "Risk Monitoring",
            "action": "Implement enhanced monthly NPL tracking dashboard for risk committee review.",
            "timeline": "60 days"
        })
    
    return recommendations

# ─── Individual Data Entry & Computation ──────────────────────────────────────
def compute_risk_metrics(data):
    """Compute risk metrics from individual input"""
    try:
        rcfe = float(data.get("rcfe_input", 0.5))
        npl = float(data.get("npl_input", 5.0))
        car = float(data.get("car_input", 15.0))
        roa = float(data.get("roa_input", 1.0))
        
        rcfe_score = rcfe * 100
        npl_risk = min(100, (npl / 20) * 100)
        car_risk = max(0, (20 - min(20, car)) / 20 * 100)
        
        composite_risk = (npl_risk * 0.4 + (100 - rcfe_score) * 0.3 + car_risk * 0.3)
        
        if composite_risk >= 60:
            risk_level = "Critical"
        elif composite_risk >= 40:
            risk_level = "Elevated"
        elif composite_risk >= 20:
            risk_level = "Moderate"
        else:
            risk_level = "Low"
        
        return {
            "rcfe_score": rcfe_score,
            "npl_risk": npl_risk,
            "car_risk": car_risk,
            "composite_risk": composite_risk,
            "risk_level": risk_level,
            "rcfe_adequate": rcfe_score >= 60,
            "npl_critical": npl > 7
        }
    except Exception as e:
        return {"error": str(e)}

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
.rcfe-high { background: rgba(0, 229, 160, 0.1); border-left: 3px solid #00E5A0; }
.rcfe-mid { background: rgba(255, 181, 71, 0.1); border-left: 3px solid #FFB547; }
.rcfe-low { background: rgba(255, 77, 106, 0.1); border-left: 3px solid #FF4D6A; }
.member-card { background: #111827; border: 1px solid #2A3347; border-radius: 8px; padding: 12px; margin: 8px 0; }
.report-header { background: #111827; border-bottom: 1px solid #2A3347; padding: 16px; border-radius: 8px 8px 0 0; }
.report-section { margin: 16px 0; }
.report-section-title { font-weight: 700; margin: 12px 0 8px; color: #00E5A0; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; }
.kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 12px 0; }
.kpi-item { background: #111827; padding: 12px; border-radius: 6px; text-align: center; }
.kpi-label { font-size: 11px; color: #6B7A99; text-transform: uppercase; }
.kpi-value { font-size: 20px; font-weight: 700; }
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
    # Load ZB Bank data
    zb_data = load_zb_bank_data()
    rc_members = get_risk_committee_members()
    
    # Sidebar
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
            "📊 Chapter 4 Analysis",
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
        <div style='font-size:14px;color:#6B7A99'>Chapter 4: Empirical Analysis & Decision Support System</div>
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
            st.metric("Current NPL Ratio", f"{latest['NPL_Ratio']:.1f}%", 
                      delta=f"{latest['NPL_Ratio'] - 7:.1f}% vs 7% threshold", delta_color="inverse")
        with col2:
            rcfe_pct = latest['RCFE'] * 100
            st.metric("RCFE Score", f"{rcfe_pct:.0f}%", delta="Target: 60%")
        with col3:
            st.metric("Capital Adequacy", f"{latest['Capital_Adequacy']:.1f}%", delta="Min: 12%")
        with col4:
            st.metric("ROA", f"{latest['ROA']:.1f}%", delta="Industry avg: 1.5%")
        with col5:
            st.metric("Loan-to-Deposit", f"{latest['Loan_to_Deposit']:.0f}%")
        
        col_a, col_b = st.columns(2)
        with col_a:
            fig = px.line(zb_data, x="Year", y="NPL_Ratio", 
                         title="ZB Bank NPL Ratio Trend (2013-2024)",
                         markers=True, line_shape="spline")
            fig.add_hline(y=7, line_dash="dash", line_color="#FF4D6A", annotation_text="7% Critical Threshold")
            fig.add_hline(y=5, line_dash="dash", line_color="#FFB547", annotation_text="5% Warning Threshold")
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            
        with col_b:
            fig = px.line(zb_data, x="Year", y="RCFE", 
                         title="Risk Committee Financial Expertise Trend",
                         markers=True, line_shape="spline")
            fig.add_hline(y=0.6, line_dash="dash", line_color="#00E5A0", annotation_text="Target 60%")
            fig.add_hline(y=0.5, line_dash="dash", line_color="#FFB547", annotation_text="Minimum 50%")
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        
        col_c, col_d = st.columns(2)
        with col_c:
            fig = px.scatter(zb_data, x="RCFE", y="NPL_Ratio", color="Year",
                           size="Capital_Adequacy", title="RCFE vs NPL Ratio Correlation")
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            corr = zb_data["RCFE"].corr(zb_data["NPL_Ratio"])
            st.caption(f"📊 Pearson Correlation: r = {corr:.3f}")
        
        with col_d:
            recent = zb_data[zb_data["Year"] >= 2020][["Year", "NPL_Ratio", "RCFE", "Capital_Adequacy", "ROA"]]
            recent = recent.set_index("Year").T
            fig = px.imshow(recent, text_auto=True, aspect="auto", color_continuous_scale="RdYlGn",
                           title="Key Metrics Heatmap (2020-2024)")
            fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    
    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 2: RISK COMMITTEE EXPERTISE
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "👥 Risk Committee Expertise":
        st.markdown('<div class="section-header">Risk Committee Financial Expertise Analysis</div>', unsafe_allow_html=True)
        
        latest = zb_data[zb_data["Year"] == zb_data["Year"].max()].iloc[0]
        current_rcfe = latest["RCFE"] * 100
        current_npl = latest["NPL_Ratio"]
        
        status, icon, message = assess_rcfe_adequacy(current_rcfe)
        status_color = "#00E5A0" if status == "Adequate" else "#FFB547" if status == "Moderate" else "#FF4D6A"
        
        st.markdown(f"""
        <div class='card'>
            <div style='display:flex; justify-content:space-between; align-items:center'>
                <div>
                    <div style='font-size:14px;color:#6B7A99'>Risk Committee Financial Expertise Score</div>
                    <div style='font-size:48px;font-weight:700;color:{status_color}'>{current_rcfe:.0f}%</div>
                    <div style='font-size:12px;margin-top:8px'>{icon} {status} - {message}</div>
                </div>
                <div style='text-align:center'>
                    <div style='font-size:14px;color:#6B7A99'>Current NPL Ratio</div>
                    <div style='font-size:36px;font-weight:700;color:{"#FF4D6A" if current_npl>7 else "#FFB547" if current_npl>5 else "#00E5A0"}'>{current_npl:.1f}%</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Current Risk Committee Members</div>', unsafe_allow_html=True)
        
        cols = st.columns(4)
        for idx, (_, member) in enumerate(rc_members.iterrows()):
            with cols[idx % 4]:
                expertise_color = "#00E5A0" if member["Expertise_Score"] >= 80 else "#FFB547" if member["Expertise_Score"] >= 70 else "#FF4D6A"
                st.markdown(f"""
                <div class='member-card'>
                    <div style='font-weight:700;font-size:14px'>{member['Name']}</div>
                    <div style='font-size:11px;color:#6B7A99;margin:4px 0'>{member['Position']}</div>
                    <div style='font-size:11px;color:#6B7A99'>{member['Qualifications']}</div>
                    <hr style='margin:8px 0;border-color:#2A3347'>
                    <div style='display:flex;justify-content:space-between;font-size:11px'>
                        <span>Expertise: <span style='color:{expertise_color}'>{member['Expertise_Score']}/100</span></span>
                        <span>Experience: {member['Risk_Experience_Years']} yrs</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">📋 Targeted Recommendations</div>', unsafe_allow_html=True)
        
        recommendations = get_rcfe_recommendations(current_rcfe, current_npl)
        for rec in recommendations:
            priority_color = "#FF4D6A" if rec["priority"] == "CRITICAL" else "#FFB547" if rec["priority"] == "HIGH" else "#00E5A0"
            st.markdown(f"""
            <div class='card'>
                <div style='display:flex; justify-content:space-between'>
                    <div>
                        <div style='font-weight:700;color:{priority_color}'>{rec['priority']} PRIORITY</div>
                        <div style='font-size:14px;font-weight:600;margin:4px 0'>{rec['area']}</div>
                        <div style='font-size:13px;color:#B0BAD0'>{rec['action']}</div>
                    </div>
                    <div style='font-size:11px;color:#6B7A99;background:#111827;padding:4px 8px;border-radius:4px'>{rec['timeline']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=zb_data["Year"], y=zb_data["RCFE"] * 100,
                                 mode="lines+markers", name="RCFE %",
                                 line=dict(color="#00E5A0", width=3),
                                 marker=dict(size=8, color="#00E5A0")))
        fig.add_hline(y=60, line_dash="dash", line_color="#00E5A0", annotation_text="Target (60%)")
        fig.add_hline(y=50, line_dash="dash", line_color="#FFB547", annotation_text="Minimum (50%)")
        fig.update_layout(title="Risk Committee Financial Expertise Over Time",
                         yaxis_title="RCFE (%)", xaxis_title="Year",
                         height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
    
    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 3: CHAPTER 4 ANALYSIS
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "📊 Chapter 4 Analysis":
        st.markdown('<div class="section-header">Chapter 4: Empirical Findings & Hypothesis Testing</div>', unsafe_allow_html=True)
        
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
                {"✅ <b>H₀ REJECTED</b> — RCFE has a significant negative effect on NPL ratio" if corr < -0.3 else "⚠️ Weak correlation — More data needed to reject H₀"}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Key Findings from Empirical Analysis</div>', unsafe_allow_html=True)
        
        findings = [
            {"finding": "RCFE and NPL Correlation", "result": f"{corr:.3f}", 
             "interpretation": "Negative correlation indicates higher expertise → lower credit risk",
             "supports_hypothesis": corr < 0},
            {"finding": "RCFE Improvement Trend", "result": f"+{(zb_data['RCFE'].iloc[-1] - zb_data['RCFE'].iloc[0]) * 100:.0f}%",
             "interpretation": "ZB Bank has improved risk committee expertise over time",
             "supports_hypothesis": True},
            {"finding": "NPL Reduction", "result": f"{(zb_data['NPL_Ratio'].iloc[0] - zb_data['NPL_Ratio'].iloc[-1]):.1f}%",
             "interpretation": f"Significant reduction from 19.5% to {zb_data['NPL_Ratio'].iloc[-1]:.1f}%",
             "supports_hypothesis": True},
        ]
        
        for f in findings:
            icon = "✅" if f["supports_hypothesis"] else "❌" if f["supports_hypothesis"] is False else "📌"
            st.markdown(f"""
            <div class='card'>
                <div style='display:flex; justify-content:space-between'>
                    <span style='font-weight:700'>{f['finding']}</span>
                    <span style='color:#00E5A0'>{f['result']}</span>
                </div>
                <div style='font-size:13px;color:#B0BAD0;margin-top:8px'>{icon} {f['interpretation']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="section-header">Panel Regression Analysis</div>', unsafe_allow_html=True)
        
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
        
        with st.expander("📐 Full Regression Output"):
            st.code(model.summary().as_text())
    
    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 4: INDIVIDUAL COMPUTATION
    # ──────────────────────────────────────────────────────────────────────────
    elif page == "📝 Individual Computation":
        st.markdown('<div class="section-header">Individual Risk Computation</div>', unsafe_allow_html=True)
        st.markdown("Enter loan or risk data to compute credit risk metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Enter Risk Parameters")
            rcfe_input = st.slider("Risk Committee Financial Expertise (RCFE)", 0.0, 1.0, 0.55, 0.01)
            npl_input = st.number_input("NPL Ratio (%)", 0.0, 30.0, 5.0, 0.1)
            car_input = st.number_input("Capital Adequacy Ratio (%)", 0.0, 35.0, 15.0, 0.1)
            roa_input = st.number_input("Return on Assets (ROA %)", -5.0, 10.0, 1.0, 0.1)
            
            if st.button("🔄 Compute Risk Metrics", use_container_width=True):
                results = compute_risk_metrics({
                    "rcfe_input": rcfe_input, "npl_input": npl_input,
                    "car_input": car_input, "roa_input": roa_input
                })
                if "error" not in results:
                    st.session_state.individual_input = results
                    st.success("Computation complete!")
                else:
                    st.error(f"Error: {results['error']}")
        
        with col2:
            st.markdown("### 📈 Computation Results")
            if st.session_state.individual_input:
                res = st.session_state.individual_input
                risk_color = "#FF4D6A" if res["risk_level"] == "Critical" else "#FFB547" if res["risk_level"] == "Elevated" else "#00E5A0"
                
                st.markdown(f"""
                <div class='card'>
                    <div style='text-align:center'>
                        <div style='font-size:12px;color:#6B7A99'>Composite Risk Score</div>
                        <div style='font-size:48px;font-weight:700;color:{risk_color}'>{res['composite_risk']:.1f}/100</div>
                        <div style='font-size:14px;color:{risk_color}'>Risk Level: {res['risk_level']}</div>
                    </div>
                    <hr>
                    <div><b>RCFE Score:</b> {res['rcfe_score']:.0f}% {'✅ Adequate' if res['rcfe_adequate'] else '⚠️ Below target'}</div>
                    <div><b>NPL Risk Score:</b> {res['npl_risk']:.1f}/100</div>
                    <div><b>Capital Risk Score:</b> {res['car_risk']:.1f}/100</div>
                </div>
                """, unsafe_allow_html=True)
                
                if res["npl_critical"]:
                    st.warning("⚠️ NPL ratio exceeds critical threshold (7%)")
                if not res["rcfe_adequate"]:
                    st.warning("⚠️ RCFE below 60% target")
            else:
                st.info("Enter parameters and click 'Compute'")
        
        latest = zb_data[zb_data["Year"] == zb_data["Year"].max()].iloc[0]
        comp_col1, comp_col2, comp_col3 = st.columns(3)
        with comp_col1:
            st.metric("Current ZB Bank NPL", f"{latest['NPL_Ratio']:.1f}%")
        with comp_col2:
            st.metric("Current ZB Bank RCFE", f"{latest['RCFE'] * 100:.0f}%")
        with comp_col3:
            st.metric("Current ZB Bank CAR", f"{latest['Capital_Adequacy']:.1f}%")
    
    # ──────────────────────────────────────────────────────────────────────────
    # PAGE 5: REPORTS & WARNINGS - FIXED VERSION with proper HTML rendering
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
        
        if latest["Capital_Adequacy"] < 12:
            warnings_list.append(("CRITICAL", f"Capital Adequacy at {latest['Capital_Adequacy']:.1f}% below regulatory minimum", "Immediate capital injection required"))
        
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
            st.success("✅ No active warnings. All key metrics within acceptable ranges.")
        
        # Board Report - FIXED: Using st.markdown with proper HTML and separate containers
        st.markdown('<div class="section-header">📋 Board Risk Committee Report</div>', unsafe_allow_html=True)
        
        report_date = datetime.datetime.now().strftime("%d %B %Y")
        
        # Report header - separate container
        with st.container():
            st.markdown(f"""
            <div style='background:#111827; border:1px solid #2A3347; border-radius:8px; overflow:hidden; margin-bottom:16px'>
                <div style='background:#1C2333; padding:12px 16px; border-bottom:1px solid #2A3347'>
                    <div style='font-family:"IBM Plex Mono"; font-size:10px; color:#6B7A99'>CONFIDENTIAL - BOARD RISK COMMITTEE</div>
                    <div style='font-size:18px; font-weight:700; margin:4px 0'>Quarterly Credit Risk Oversight Report</div>
                    <div style='font-size:12px; color:#6B7A99'>{report_date} | ZB Bank Limited</div>
                </div>
                <div style='padding:16px'>
            """, unsafe_allow_html=True)
            
            # Executive Summary
            st.markdown("""
            <div style='margin-bottom:20px'>
                <div style='font-weight:700; margin:0 0 8px 0; color:#00E5A0; text-transform:uppercase; font-size:12px; letter-spacing:1px'>📌 Executive Summary</div>
            </div>
            """, unsafe_allow_html=True)
            
            npl_color = "#FF4D6A" if latest["NPL_Ratio"] > 7 else "#FFB547" if latest["NPL_Ratio"] > 5 else "#00E5A0"
            rcfe_color = "#00E5A0" if current_rcfe >= 60 else "#FFB547"
            
            st.markdown(f"""
            <div style='font-size:14px; color:#B0BAD0; margin-bottom:20px'>
                As of <b>{latest['Year']}</b>, ZB Bank recorded an NPL ratio of <b style='color:{npl_color}'>{latest['NPL_Ratio']:.1f}%</b> 
                against a target threshold of 7%. The Risk Committee Financial Expertise (RCFE) stands at <b style='color:{rcfe_color}'>{current_rcfe:.0f}%</b>, 
                which is {'above' if current_rcfe >= 60 else 'below'} the recommended 60% threshold.
            </div>
            """, unsafe_allow_html=True)
            
            # Key Risk Indicators - using columns for better display
            st.markdown("""
            <div style='margin-bottom:20px'>
                <div style='font-weight:700; margin:0 0 12px 0; color:#00E5A0; text-transform:uppercase; font-size:12px; letter-spacing:1px'>📊 Key Risk Indicators</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Create 3 columns for KPI display using st.columns for better rendering
            kpi_cols = st.columns(3)
            metrics = [
                ("NPL Ratio", f"{latest['NPL_Ratio']:.1f}%", npl_color),
                ("RCFE", f"{current_rcfe:.0f}%", rcfe_color),
                ("Capital Adequacy", f"{latest['Capital_Adequacy']:.1f}%", "#00E5A0" if latest["Capital_Adequacy"] >= 12 else "#FF4D6A"),
                ("ROA", f"{latest['ROA']:.1f}%", "#E2E8F0"),
                ("Loan-to-Deposit", f"{latest['Loan_to_Deposit']:.0f}%", "#E2E8F0"),
                ("RC Size", f"{latest['RC_Size']} members", "#E2E8F0")
            ]
            
            for idx, (label, value, color) in enumerate(metrics):
                with kpi_cols[idx % 3]:
                    st.markdown(f"""
                    <div style='background:#111827; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center'>
                        <div style='font-size:11px; color:#6B7A99; text-transform:uppercase'>{label}</div>
                        <div style='font-size:20px; font-weight:700; color:{color}'>{value}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Risk Committee Composition
            st.markdown("""
            <div style='margin:20px 0 16px 0'>
                <div style='font-weight:700; margin:0 0 12px 0; color:#00E5A0; text-transform:uppercase; font-size:12px; letter-spacing:1px'>👥 Risk Committee Composition</div>
            </div>
            """, unsafe_allow_html=True)
            
            for _, member in rc_members.iterrows():
                st.markdown(f"""
                <div style='background:#111827; padding:10px 12px; border-radius:6px; margin-bottom:8px'>
                    <span style='font-weight:600'>{member['Name']}</span><br>
                    <span style='font-size:12px; color:#6B7A99'>{member['Position']} - {member['Qualifications']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Recommendations
            st.markdown("""
            <div style='margin:20px 0 16px 0'>
                <div style='font-weight:700; margin:0 0 12px 0; color:#00E5A0; text-transform:uppercase; font-size:12px; letter-spacing:1px'>📋 Recommendations</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <ol style='color:#B0BAD0; margin-left:20px'>
                <li>Maintain current NPL monitoring frequency with monthly dashboard updates</li>
                <li>Consider recruiting additional CFA-certified member to improve RCFE to 60%</li>
                <li>Schedule next risk committee meeting for quarterly portfolio review</li>
            </ol>
            """, unsafe_allow_html=True)
            
            # Footer
            st.markdown("""
            <hr style='border-color:#2A3347; margin:16px 0'>
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
                "capital_adequacy": float(latest["Capital_Adequacy"]),
                "roa": float(latest["ROA"]),
                "loan_to_deposit": float(latest["Loan_to_Deposit"])
            },
            "warnings": len(warnings_list),
            "rcfe_adequate": bool(current_rcfe >= 60)
        }
        
        report_json = json.dumps(report_data, indent=2, default=convert_to_serializable)
        
        st.download_button("⬇ Download Full Report (JSON)", 
                          report_json,
                          file_name=f"zb_bank_risk_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                          mime="application/json")

# ─── Run App ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if st.session_state.authenticated:
        main_app()
    else:
        show_login()
