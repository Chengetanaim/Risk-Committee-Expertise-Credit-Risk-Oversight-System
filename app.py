import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RCECOS | Risk Committee Expertise & Credit Risk Oversight",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Barlow+Condensed:wght@300;500;700&family=Barlow:wght@300;400;500&display=swap');

/* Root & global */
:root {
    --bg: #0B0F1A;
    --surface: #111827;
    --surface2: #1C2333;
    --border: #2A3347;
    --accent: #00E5A0;
    --accent2: #0091FF;
    --warn: #FFB547;
    --danger: #FF4D6A;
    --text: #E2E8F0;
    --muted: #6B7A99;
    --mono: 'IBM Plex Mono', monospace;
    --head: 'Barlow Condensed', sans-serif;
    --body: 'Barlow', sans-serif;
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--body) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* Headers */
h1, h2, h3, h4 {
    font-family: var(--head) !important;
    letter-spacing: 0.03em !important;
    color: var(--text) !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 12px !important;
}
[data-testid="metric-container"] label {
    font-family: var(--mono) !important;
    font-size: 11px !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: var(--head) !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    color: var(--accent) !important;
}
[data-testid="stMetricDelta"] { font-family: var(--mono) !important; font-size: 12px !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--mono) !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--muted) !important;
    background: transparent !important;
    border: none !important;
    padding: 12px 20px !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* Buttons */
.stButton > button {
    background: var(--accent) !important;
    color: #0B0F1A !important;
    font-family: var(--mono) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    border: none !important;
    border-radius: 4px !important;
    padding: 8px 20px !important;
}
.stButton > button:hover {
    background: #00c98a !important;
    transform: translateY(-1px);
}

/* Selectbox / inputs */
.stSelectbox > div, .stNumberInput > div, .stTextInput > div {
    background: var(--surface2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
.stSelectbox label, .stNumberInput label, .stTextInput label, .stSlider label, .stRadio label, .stCheckbox label {
    font-family: var(--mono) !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--muted) !important;
}

/* DataFrames */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* Dividers */
hr { border-color: var(--border) !important; }

/* Alert boxes */
.stAlert { border-radius: 6px !important; }

/* Custom card */
.card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.card-title {
    font-family: var(--mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--muted);
    margin-bottom: 8px;
}
.card-value {
    font-family: var(--head);
    font-size: 22px;
    font-weight: 700;
    color: var(--text);
}

/* Warning badge */
.badge-danger { color: var(--danger); font-family: var(--mono); font-size: 11px; font-weight: 600; }
.badge-warn   { color: var(--warn);   font-family: var(--mono); font-size: 11px; font-weight: 600; }
.badge-ok     { color: var(--accent); font-family: var(--mono); font-size: 11px; font-weight: 600; }

/* Section header line */
.section-header {
    font-family: var(--head);
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.05em;
    border-left: 3px solid var(--accent);
    padding-left: 12px;
    margin: 20px 0 16px 0;
    text-transform: uppercase;
}

/* Score ring */
.score-ring {
    text-align: center;
    padding: 12px;
}
.score-number {
    font-family: var(--head);
    font-size: 48px;
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
}
.score-label {
    font-family: var(--mono);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-top: 4px;
}
</style>
""", unsafe_allow_html=True)

# ─── Seed Data ────────────────────────────────────────────────────────────────
np.random.seed(42)
BANKS = ["CBZ Bank", "ZB Bank", "Steward Bank", "NMB Bank", "BancABC", "Ecobank Zimbabwe", "FBC Bank"]
YEARS = list(range(2018, 2025))

@st.cache_data
def generate_bank_data():
    rows = []
    for bank in BANKS:
        base_npl = np.random.uniform(3, 12)
        for year in YEARS:
            trend = (year - 2018) * np.random.uniform(-0.3, 0.5)
            npl = max(1, base_npl + trend + np.random.normal(0, 0.8))
            rows.append({
                "Bank": bank, "Year": year,
                "NPL_Ratio": round(npl, 2),
                "Sector_Exposure_Agriculture": round(np.random.uniform(5, 25), 1),
                "Sector_Exposure_Mining": round(np.random.uniform(5, 20), 1),
                "Sector_Exposure_Manufacturing": round(np.random.uniform(10, 30), 1),
                "Overdue_Facilities_pct": round(npl * np.random.uniform(0.8, 1.4), 2),
                "Provisioning_Coverage": round(np.random.uniform(40, 90), 1),
                "Capital_Adequacy": round(np.random.uniform(10, 20), 2),
                "LDR": round(np.random.uniform(50, 90), 1),
                "ROA": round(np.random.uniform(0.5, 3.5), 2),
            })
    return pd.DataFrame(rows)

@st.cache_data
def generate_committee_members():
    names = [
        ("Dr. Faith Chikwanda", "CBZ Bank"), ("Mr. Tawanda Moyo", "CBZ Bank"),
        ("Ms. Rudo Sibanda", "CBZ Bank"), ("Prof. Tafadzwa Ncube", "ZB Bank"),
        ("Mr. Charles Mutasa", "ZB Bank"), ("Mrs. Grace Mapondera", "ZB Bank"),
        ("Dr. John Muza", "Steward Bank"), ("Ms. Tsitsi Hlupeko", "Steward Bank"),
        ("Mr. Simba Kurasha", "NMB Bank"), ("Dr. Nyarai Banda", "NMB Bank"),
        ("Mrs. Anesu Chigumira", "BancABC"), ("Mr. Kudakwashe Dube", "BancABC"),
        ("Prof. Munyaradzi Juru", "Ecobank Zimbabwe"), ("Ms. Tatenda Gwanetsa", "Ecobank Zimbabwe"),
        ("Dr. Farai Makwara", "FBC Bank"), ("Mr. Paidamoyo Zvimba", "FBC Bank"),
    ]
    qualifications = ["PhD Finance", "CFA", "CA(Z)", "MBA Finance", "MSc Banking", "ACCA", "CPA", "FRM"]
    experience_ranges = [(5, 10), (10, 15), (15, 20), (20, 30), (3, 7)]
    rows = []
    for name, bank in names:
        qual_count = np.random.randint(1, 4)
        quals = np.random.choice(qualifications, qual_count, replace=False).tolist()
        low, high = experience_ranges[np.random.randint(len(experience_ranges))]
        yrs_exp = np.random.randint(low, high)
        has_risk = np.random.choice([True, False], p=[0.6, 0.4])
        has_board = np.random.choice([True, False], p=[0.7, 0.3])
        score = min(100, (
            (20 if "PhD" in " ".join(quals) or "Prof" in name else 10 if "MBA" in " ".join(quals) else 5) +
            (25 if "CFA" in quals or "FRM" in quals else 15 if "CA(Z)" in quals or "ACCA" in quals else 8) +
            min(30, yrs_exp * 1.5) +
            (15 if has_risk else 0) +
            (10 if has_board else 0)
        ))
        rows.append({
            "Name": name, "Bank": bank,
            "Qualifications": ", ".join(quals),
            "Years_Experience": yrs_exp,
            "Risk_Management_Certified": has_risk,
            "Board_Director_Experience": has_board,
            "Expertise_Score": round(score),
            "Role": np.random.choice(["Chairperson", "Member", "Independent Member"], p=[0.2, 0.5, 0.3]),
        })
    return pd.DataFrame(rows)

bank_df = generate_bank_data()
committee_df = generate_committee_members()

# ─── Helpers ──────────────────────────────────────────────────────────────────
PLOT_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="IBM Plex Mono",
    font_color="#E2E8F0",
    colorway=["#00E5A0", "#0091FF", "#FFB547", "#FF4D6A", "#A78BFA", "#FB7185", "#34D399"],
    xaxis=dict(showgrid=False, color="#6B7A99", linecolor="#2A3347"),
    yaxis=dict(showgrid=True, gridcolor="#1C2333", color="#6B7A99", linecolor="#2A3347"),
)

def apply_theme(fig):
    fig.update_layout(**PLOT_THEME)
    return fig

def risk_badge(npl):
    if npl >= 10:  return "🔴 CRITICAL"
    elif npl >= 7: return "🟠 ELEVATED"
    elif npl >= 4: return "🟡 MODERATE"
    else:          return "🟢 ACCEPTABLE"

def expertise_badge(score):
    if score >= 75:   return "🟢 HIGH"
    elif score >= 50: return "🟡 MODERATE"
    else:             return "🔴 LOW"

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:16px 0 8px'>
      <div style='font-family:"IBM Plex Mono",monospace;font-size:10px;color:#6B7A99;letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px'>System</div>
      <div style='font-family:"Barlow Condensed",sans-serif;font-size:22px;font-weight:700;color:#E2E8F0;line-height:1.1'>RCECOS<br><span style='color:#00E5A0'>Risk Oversight</span></div>
      <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;margin-top:6px;letter-spacing:.06em'>Zimbabwe Banking Sector · v1.0</div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    st.markdown("**FILTERS**")
    selected_bank = st.selectbox("Bank", ["All Banks"] + BANKS)
    selected_year = st.selectbox("Year", ["All Years"] + [str(y) for y in YEARS], index=len(YEARS))
    npl_threshold = st.slider("NPL Warning Threshold (%)", 1.0, 20.0, 7.0, 0.5)

    st.markdown("---")
    st.markdown("""
    <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;line-height:1.8'>
    HIT400 RESEARCH<br>
    Tadiwa Chokuona · H220460J<br>
    Dept. Forensic Accounting<br>
    & Auditing
    </div>
    """, unsafe_allow_html=True)

# ─── Filter helpers ───────────────────────────────────────────────────────────
def filter_bank_df():
    df = bank_df.copy()
    if selected_bank != "All Banks":
        df = df[df["Bank"] == selected_bank]
    if selected_year != "All Years":
        df = df[df["Year"] == int(selected_year)]
    return df

def filter_committee_df():
    df = committee_df.copy()
    if selected_bank != "All Banks":
        df = df[df["Bank"] == selected_bank]
    return df

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:24px'>
  <div>
    <div style='font-family:"IBM Plex Mono",monospace;font-size:11px;color:#6B7A99;text-transform:uppercase;letter-spacing:.12em'>Risk Committee Expertise & Credit Risk Oversight System</div>
    <div style='font-family:"Barlow Condensed",sans-serif;font-size:36px;font-weight:700;letter-spacing:.04em;line-height:1;margin-top:2px'>DECISION SUPPORT DASHBOARD</div>
  </div>
  <div style='font-family:"IBM Plex Mono",monospace;font-size:11px;color:#00E5A0;text-align:right'>
    ZIMBABWEAN BANKS<br>
    <span style='color:#6B7A99'>2018 – 2024</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── KPI Row ──────────────────────────────────────────────────────────────────
fdf = filter_bank_df()
cdf = filter_committee_df()

avg_npl = fdf["NPL_Ratio"].mean()
avg_expertise = cdf["Expertise_Score"].mean() if not cdf.empty else 0
avg_provision = fdf["Provisioning_Coverage"].mean()
avg_cap = fdf["Capital_Adequacy"].mean()
flagged = (fdf["NPL_Ratio"] >= npl_threshold).sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Avg NPL Ratio", f"{avg_npl:.1f}%", delta=f"{avg_npl - 7:.1f}% vs 7% benchmark", delta_color="inverse")
k2.metric("Avg Expertise Score", f"{avg_expertise:.0f}/100", delta="Committee Quality")
k3.metric("Provisioning Coverage", f"{avg_provision:.0f}%", delta="Loan loss reserves")
k4.metric("Capital Adequacy", f"{avg_cap:.1f}%", delta=f"{'Above' if avg_cap > 12 else 'Below'} 12% floor")
k5.metric("⚠ Flagged Observations", str(int(flagged)), delta=f"NPL ≥ {npl_threshold}%", delta_color="inverse")

st.markdown("---")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 OVERVIEW",
    "👥 COMMITTEE EXPERTISE",
    "📉 CREDIT RISK INDICATORS",
    "🚨 EARLY WARNING",
    "📋 REPORTING"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Sector Overview</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        # NPL trend across all banks
        pivot = bank_df.groupby(["Year", "Bank"])["NPL_Ratio"].mean().reset_index()
        fig = px.line(pivot, x="Year", y="NPL_Ratio", color="Bank",
                      title="NPL Ratio Trends by Bank (2018–2024)",
                      labels={"NPL_Ratio": "NPL Ratio (%)"})
        fig.add_hline(y=npl_threshold, line_dash="dash", line_color="#FF4D6A",
                      annotation_text=f"Threshold {npl_threshold}%",
                      annotation_font_color="#FF4D6A")
        fig.update_traces(line_width=2)
        apply_theme(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # Expertise vs NPL scatter (latest year)
        latest = bank_df[bank_df["Year"] == 2024].copy()
        exp_avg = committee_df.groupby("Bank")["Expertise_Score"].mean().reset_index()
        exp_avg.columns = ["Bank", "Avg_Expertise"]
        merged = latest.merge(exp_avg, on="Bank")
        fig2 = px.scatter(merged, x="Avg_Expertise", y="NPL_Ratio", color="Bank",
                          size="Capital_Adequacy", hover_name="Bank",
                          title="Expertise vs NPL (2024)",
                          labels={"Avg_Expertise": "Committee Expertise Score", "NPL_Ratio": "NPL Ratio (%)"})
        fig2.update_traces(marker_line_width=1, marker_line_color="#0B0F1A")
        apply_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    # Summary table
    st.markdown('<div class="section-header">Bank-Level Snapshot</div>', unsafe_allow_html=True)
    snap = bank_df[bank_df["Year"] == 2024].merge(
        committee_df.groupby("Bank")["Expertise_Score"].mean().round(1).reset_index(),
        on="Bank"
    ).rename(columns={"Expertise_Score": "Avg Expertise"})
    snap["Risk Level"] = snap["NPL_Ratio"].apply(risk_badge)
    snap["Expertise Level"] = snap["Avg Expertise"].apply(expertise_badge)
    display_cols = ["Bank", "NPL_Ratio", "Avg Expertise", "Provisioning_Coverage", "Capital_Adequacy", "Risk Level", "Expertise Level"]
    st.dataframe(snap[display_cols].rename(columns={
        "NPL_Ratio": "NPL Ratio (%)",
        "Provisioning_Coverage": "Provision Cover (%)",
        "Capital_Adequacy": "CAR (%)"
    }), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — COMMITTEE EXPERTISE
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Risk Committee Member Profiles</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        # Expertise scores per bank
        fig3 = px.box(committee_df, x="Bank", y="Expertise_Score", color="Bank",
                      title="Expertise Score Distribution by Bank",
                      labels={"Expertise_Score": "Score (0–100)"})
        fig3.update_traces(boxmean=True)
        apply_theme(fig3)
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        # Role distribution
        role_counts = cdf["Role"].value_counts().reset_index()
        role_counts.columns = ["Role", "Count"]
        fig4 = px.pie(role_counts, names="Role", values="Count",
                      title="Committee Composition",
                      hole=0.55)
        fig4.update_traces(textfont_family="IBM Plex Mono", textfont_size=10)
        apply_theme(fig4)
        st.plotly_chart(fig4, use_container_width=True)

    # Add / Edit member form
    st.markdown('<div class="section-header">Register Committee Member</div>', unsafe_allow_html=True)
    with st.expander("➕  Add New Member", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            m_name = st.text_input("Full Name")
            m_bank = st.selectbox("Bank", BANKS, key="m_bank")
            m_role = st.selectbox("Role", ["Member", "Chairperson", "Independent Member"])
        with f2:
            m_quals = st.multiselect("Qualifications", ["PhD Finance","CFA","CA(Z)","MBA Finance","MSc Banking","ACCA","CPA","FRM","BCom Finance"])
            m_exp = st.number_input("Years of Experience", 0, 50, 5)
        with f3:
            m_risk_cert = st.checkbox("Risk Management Certified")
            m_board_exp = st.checkbox("Board Director Experience")
            if st.button("Compute & Save"):
                score = min(100, (
                    (20 if any("PhD" in q or "Prof" in q for q in m_quals) else 10 if "MBA Finance" in m_quals else 5) +
                    (25 if "CFA" in m_quals or "FRM" in m_quals else 15 if "CA(Z)" in m_quals or "ACCA" in m_quals else 8) +
                    min(30, m_exp * 1.5) + (15 if m_risk_cert else 0) + (10 if m_board_exp else 0)
                ))
                st.success(f"✅ {m_name} — Computed Expertise Score: **{score:.0f}/100** ({expertise_badge(score)})")

    # Member table
    st.markdown("**Committee Directory**")
    display_df = cdf[["Name","Bank","Role","Qualifications","Years_Experience","Risk_Management_Certified","Board_Director_Experience","Expertise_Score"]].copy()
    display_df["Expertise_Score"] = display_df["Expertise_Score"].apply(lambda x: f"{x}/100")
    display_df.columns = ["Name","Bank","Role","Qualifications","Exp (yrs)","Risk Cert","Board Exp","Score"]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Correlation between expertise and NPL
    st.markdown('<div class="section-header">Expertise — Credit Risk Relationship</div>', unsafe_allow_html=True)
    exp_avg = committee_df.groupby("Bank")["Expertise_Score"].mean().reset_index()
    exp_avg.columns = ["Bank", "Avg_Expertise"]
    merged_all = bank_df.merge(exp_avg, on="Bank")
    fig5 = px.scatter(merged_all, x="Avg_Expertise", y="NPL_Ratio",
                      color="Year", size="Provisioning_Coverage",
                      trendline="ols", trendline_color_override="#00E5A0",
                      title="Committee Expertise Score vs NPL Ratio (All Years, All Banks)",
                      labels={"Avg_Expertise": "Avg Expertise Score", "NPL_Ratio": "NPL Ratio (%)"})
    apply_theme(fig5)
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("OLS trendline — a downward slope supports H₁: higher expertise → lower NPL")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CREDIT RISK INDICATORS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Credit Risk Dashboard</div>', unsafe_allow_html=True)

    sel_df = fdf.copy()

    r1c1, r1c2 = st.columns(2)

    with r1c1:
        # NPL bar
        npl_data = sel_df.groupby("Bank")["NPL_Ratio"].mean().reset_index().sort_values("NPL_Ratio", ascending=True)
        colors = ["#FF4D6A" if v >= npl_threshold else "#FFB547" if v >= npl_threshold * 0.7 else "#00E5A0"
                  for v in npl_data["NPL_Ratio"]]
        fig6 = go.Figure(go.Bar(
            x=npl_data["NPL_Ratio"], y=npl_data["Bank"], orientation="h",
            marker_color=colors, text=npl_data["NPL_Ratio"].apply(lambda x: f"{x:.1f}%"),
            textposition="outside", textfont=dict(family="IBM Plex Mono", size=10)
        ))
        fig6.add_vline(x=npl_threshold, line_dash="dash", line_color="#FF4D6A",
                       annotation_text="Threshold", annotation_font_color="#FF4D6A")
        fig6.update_layout(title="Average NPL Ratio by Bank", xaxis_title="NPL Ratio (%)", **PLOT_THEME)
        st.plotly_chart(fig6, use_container_width=True)

    with r1c2:
        # Sector exposure radar
        if selected_bank != "All Banks":
            sec = fdf[["Sector_Exposure_Agriculture", "Sector_Exposure_Mining", "Sector_Exposure_Manufacturing"]].mean()
        else:
            sec = bank_df.groupby("Bank")[["Sector_Exposure_Agriculture","Sector_Exposure_Mining","Sector_Exposure_Manufacturing"]].mean()
            sec = sec.mean()
        categories = ["Agriculture", "Mining", "Manufacturing"]
        values = [sec["Sector_Exposure_Agriculture"], sec["Sector_Exposure_Mining"], sec["Sector_Exposure_Manufacturing"]]
        values_closed = values + [values[0]]
        cats_closed = categories + [categories[0]]
        fig7 = go.Figure(go.Scatterpolar(r=values_closed, theta=cats_closed, fill="toself",
                                          fillcolor="rgba(0,229,160,0.15)", line_color="#00E5A0",
                                          name="Sector Exposure"))
        fig7.update_layout(title="Sector Exposure Concentration",
                           polar=dict(radialaxis=dict(visible=True, color="#6B7A99"),
                                      bgcolor="rgba(0,0,0,0)"),
                           **PLOT_THEME)
        st.plotly_chart(fig7, use_container_width=True)

    r2c1, r2c2 = st.columns(2)

    with r2c1:
        # Provisioning vs overdue
        fig8 = go.Figure()
        by_yr = sel_df.groupby("Year")[["Provisioning_Coverage", "Overdue_Facilities_pct"]].mean().reset_index()
        fig8.add_trace(go.Bar(x=by_yr["Year"], y=by_yr["Provisioning_Coverage"],
                               name="Provisioning Cover (%)", marker_color="#00E5A0"))
        fig8.add_trace(go.Scatter(x=by_yr["Year"], y=by_yr["Overdue_Facilities_pct"],
                                   name="Overdue Facilities (%)", mode="lines+markers",
                                   line=dict(color="#FF4D6A", width=2), marker_size=6,
                                   yaxis="y2"))
        fig8.update_layout(
            title="Provisioning Coverage vs Overdue Facilities",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_family="IBM Plex Mono",
            font_color="#E2E8F0",
            colorway=["#00E5A0", "#0091FF", "#FFB547", "#FF4D6A", "#A78BFA", "#FB7185", "#34D399"],
            xaxis=dict(showgrid=False, color="#6B7A99", linecolor="#2A3347"),
            yaxis=dict(title="Provision Cover (%)", showgrid=True, gridcolor="#1C2333", color="#6B7A99", linecolor="#2A3347"),
            yaxis2=dict(title="Overdue (%)", overlaying="y", side="right", color="#FF4D6A"),
            legend=dict(orientation="h", y=-0.2, font_family="IBM Plex Mono", font_size=10),
        )
        st.plotly_chart(fig8, use_container_width=True)

    with r2c2:
        # LDR heatmap
        ldr_piv = bank_df.pivot_table(index="Bank", columns="Year", values="LDR", aggfunc="mean").round(1)
        fig9 = go.Figure(go.Heatmap(
            z=ldr_piv.values, x=[str(c) for c in ldr_piv.columns], y=ldr_piv.index,
            colorscale=[[0, "#0B0F1A"], [0.5, "#0091FF"], [1, "#FF4D6A"]],
            text=ldr_piv.values.round(1), texttemplate="%{text}%",
            textfont=dict(family="IBM Plex Mono", size=10),
            showscale=True
        ))
        fig9.update_layout(title="Loan-to-Deposit Ratio Heatmap (%)", **PLOT_THEME)
        st.plotly_chart(fig9, use_container_width=True)

    # Manual risk entry
    st.markdown('<div class="section-header">Manual Risk Indicator Entry</div>', unsafe_allow_html=True)
    with st.expander("📝  Enter / Update Credit Risk Data", expanded=False):
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            inp_bank = st.selectbox("Bank", BANKS, key="inp_bank")
            inp_year = st.selectbox("Period", YEARS, key="inp_year")
            inp_npl = st.number_input("NPL Ratio (%)", 0.0, 50.0, 5.0, 0.1)
        with mc2:
            inp_overdue = st.number_input("Overdue Facilities (%)", 0.0, 50.0, 4.5, 0.1)
            inp_prov = st.number_input("Provisioning Coverage (%)", 0.0, 100.0, 65.0, 1.0)
            inp_ldr = st.number_input("Loan-to-Deposit Ratio (%)", 0.0, 150.0, 70.0, 1.0)
        with mc3:
            inp_cap = st.number_input("Capital Adequacy Ratio (%)", 0.0, 50.0, 14.0, 0.1)
            inp_roa = st.number_input("Return on Assets (%)", -5.0, 10.0, 1.5, 0.1)
            if st.button("Save Entry"):
                st.success(f"✅ Saved: {inp_bank} {inp_year} — NPL {inp_npl}% | Risk: {risk_badge(inp_npl)}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — EARLY WARNING
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Early Warning Mechanism</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style='font-family:"IBM Plex Mono",monospace;font-size:11px;color:#6B7A99;margin-bottom:16px'>
    Automated flags based on configurable thresholds — alerts board when indicators breach risk appetite limits
    </div>
    """, unsafe_allow_html=True)

    # Threshold config
    with st.expander("⚙️  Configure Thresholds"):
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            t_npl = st.slider("NPL Ratio Warning (%)", 1.0, 20.0, npl_threshold, 0.5, key="t_npl")
            t_npl_crit = st.slider("NPL Ratio Critical (%)", t_npl, 25.0, min(t_npl + 3, 25.0), 0.5)
        with tc2:
            t_overdue = st.slider("Overdue Facilities Warning (%)", 1.0, 20.0, 6.0, 0.5)
            t_prov = st.slider("Min Provisioning Cover (%)", 20.0, 80.0, 50.0, 5.0)
        with tc3:
            t_exp = st.slider("Min Expertise Score", 20, 90, 50, 5)
            t_cap = st.slider("Min Capital Adequacy (%)", 5.0, 20.0, 12.0, 0.5)

    # Generate alerts
    latest_data = bank_df[bank_df["Year"] == 2024].merge(
        committee_df.groupby("Bank")["Expertise_Score"].mean().round(1).reset_index().rename(
            columns={"Expertise_Score": "Avg_Expertise"}), on="Bank")

    alerts = []
    for _, row in latest_data.iterrows():
        b = row["Bank"]
        if row["NPL_Ratio"] >= t_npl_crit:
            alerts.append({"Severity": "🔴 CRITICAL", "Bank": b, "Indicator": "NPL Ratio",
                            "Value": f"{row['NPL_Ratio']:.1f}%", "Threshold": f"{t_npl_crit}%",
                            "Action": "Immediate board review + provisioning increase"})
        elif row["NPL_Ratio"] >= t_npl:
            alerts.append({"Severity": "🟠 WARNING", "Bank": b, "Indicator": "NPL Ratio",
                            "Value": f"{row['NPL_Ratio']:.1f}%", "Threshold": f"{t_npl}%",
                            "Action": "Enhanced monitoring + credit committee review"})
        if row["Overdue_Facilities_pct"] >= t_overdue:
            alerts.append({"Severity": "🟡 CAUTION", "Bank": b, "Indicator": "Overdue Facilities",
                            "Value": f"{row['Overdue_Facilities_pct']:.1f}%", "Threshold": f"{t_overdue}%",
                            "Action": "Review collections strategy"})
        if row["Provisioning_Coverage"] < t_prov:
            alerts.append({"Severity": "🟡 CAUTION", "Bank": b, "Indicator": "Provisioning Coverage",
                            "Value": f"{row['Provisioning_Coverage']:.1f}%", "Threshold": f"< {t_prov}%",
                            "Action": "Increase loan loss reserves"})
        if row["Avg_Expertise"] < t_exp:
            alerts.append({"Severity": "🟠 WARNING", "Bank": b, "Indicator": "Committee Expertise",
                            "Value": f"{row['Avg_Expertise']:.0f}/100", "Threshold": f"< {t_exp}",
                            "Action": "Board appointment review — recruit financial expert"})
        if row["Capital_Adequacy"] < t_cap:
            alerts.append({"Severity": "🔴 CRITICAL", "Bank": b, "Indicator": "Capital Adequacy",
                            "Value": f"{row['Capital_Adequacy']:.1f}%", "Threshold": f"< {t_cap}%",
                            "Action": "Urgent capital plan — notify RBZ"})

    if alerts:
        alert_df = pd.DataFrame(alerts)
        n_crit = (alert_df["Severity"].str.contains("CRITICAL")).sum()
        n_warn = (alert_df["Severity"].str.contains("WARNING")).sum()
        n_caut = (alert_df["Severity"].str.contains("CAUTION")).sum()
        a1, a2, a3 = st.columns(3)
        a1.metric("🔴 Critical Alerts", str(n_crit))
        a2.metric("🟠 Warnings", str(n_warn))
        a3.metric("🟡 Cautions", str(n_caut))
        st.dataframe(alert_df, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No alerts triggered under current thresholds.")

    # Timeline chart
    st.markdown('<div class="section-header">NPL Trajectory & Risk Zones</div>', unsafe_allow_html=True)
    b_sel = st.selectbox("Select Bank for Trajectory", BANKS, key="ew_bank")
    b_data = bank_df[bank_df["Bank"] == b_sel].sort_values("Year")
    fig10 = go.Figure()
    fig10.add_hrect(y0=0, y1=t_npl, fillcolor="rgba(0,229,160,0.06)", line_width=0, annotation_text="Safe Zone")
    fig10.add_hrect(y0=t_npl, y1=t_npl_crit, fillcolor="rgba(255,181,71,0.08)", line_width=0, annotation_text="Warning Zone")
    fig10.add_hrect(y0=t_npl_crit, y1=25, fillcolor="rgba(255,77,106,0.08)", line_width=0, annotation_text="Critical Zone")
    fig10.add_trace(go.Scatter(x=b_data["Year"], y=b_data["NPL_Ratio"],
                                mode="lines+markers+text", name="NPL Ratio",
                                line=dict(color="#00E5A0", width=3),
                                marker=dict(size=8, color="#00E5A0"),
                                text=b_data["NPL_Ratio"].apply(lambda x: f"{x:.1f}%"),
                                textposition="top center",
                                textfont=dict(family="IBM Plex Mono", size=10)))
    fig10.update_layout(title=f"NPL Trajectory — {b_sel}", yaxis_title="NPL Ratio (%)", **PLOT_THEME)
    st.plotly_chart(fig10, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — REPORTING
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Board Reporting Module</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style='font-family:"IBM Plex Mono",monospace;font-size:11px;color:#6B7A99;margin-bottom:20px'>
    Generate structured reports for board / risk committee meetings — supporting timely governance decisions
    </div>
    """, unsafe_allow_html=True)

    r_bank = st.selectbox("Bank for Report", BANKS, key="r_bank")
    r_period = st.selectbox("Reporting Period", [str(y) for y in reversed(YEARS)], key="r_period")

    r_data = bank_df[(bank_df["Bank"] == r_bank) & (bank_df["Year"] == int(r_period))]
    r_comm = committee_df[committee_df["Bank"] == r_bank]

    if not r_data.empty:
        rd = r_data.iloc[0]
        avg_exp = r_comm["Expertise_Score"].mean()

        st.markdown(f"""
        <div style='background:#111827;border:1px solid #2A3347;border-radius:8px;padding:28px 32px;margin-bottom:20px'>
          <div style='font-family:"IBM Plex Mono",monospace;font-size:10px;color:#6B7A99;text-transform:uppercase;letter-spacing:.12em'>Confidential — Board Risk Committee Report</div>
          <div style='font-family:"Barlow Condensed",sans-serif;font-size:28px;font-weight:700;margin:8px 0 4px'>CREDIT RISK OVERSIGHT REPORT</div>
          <div style='font-family:"IBM Plex Mono",monospace;font-size:12px;color:#00E5A0'>{r_bank} &nbsp;|&nbsp; Period: {r_period} &nbsp;|&nbsp; Generated: {datetime.date.today().strftime("%d %B %Y")}</div>
          <hr style='border-color:#2A3347;margin:20px 0'>

          <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;color:#E2E8F0'>1. Executive Summary</div>
          <div style='font-family:"Barlow",sans-serif;font-size:14px;color:#B0BAD0;line-height:1.7;margin-bottom:20px'>
          As at <b>{r_period}</b>, {r_bank} recorded a Non-Performing Loan (NPL) ratio of
          <span style='color:{"#FF4D6A" if rd["NPL_Ratio"] >= npl_threshold else "#00E5A0"}'><b>{rd["NPL_Ratio"]:.1f}%</b></span>
          against a monitoring threshold of {npl_threshold}%. The bank's provisioning coverage stood at
          <b>{rd["Provisioning_Coverage"]:.0f}%</b> and capital adequacy at <b>{rd["Capital_Adequacy"]:.1f}%</b>.
          The risk committee's average financial expertise score is <b>{avg_exp:.0f}/100</b>
          ({expertise_badge(avg_exp)}).
          </div>

          <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;color:#E2E8F0'>2. Key Credit Risk Indicators</div>
          <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px'>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>NPL Ratio</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:{"#FF4D6A" if rd["NPL_Ratio"] >= npl_threshold else "#00E5A0"}'>{rd["NPL_Ratio"]:.1f}%</div>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:10px;color:#6B7A99'>{risk_badge(rd["NPL_Ratio"])}</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Overdue Facilities</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:#FFB547'>{rd["Overdue_Facilities_pct"]:.1f}%</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Provisioning Cover</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:#0091FF'>{rd["Provisioning_Coverage"]:.0f}%</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Capital Adequacy</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:#00E5A0'>{rd["Capital_Adequacy"]:.1f}%</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Loan/Deposit Ratio</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:#A78BFA'>{rd["LDR"]:.0f}%</div>
            </div>
            <div style='background:#1C2333;border:1px solid #2A3347;border-radius:6px;padding:12px'>
              <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#6B7A99;text-transform:uppercase;letter-spacing:.1em'>Return on Assets</div>
              <div style='font-family:"Barlow Condensed",sans-serif;font-size:24px;font-weight:700;color:#34D399'>{rd["ROA"]:.2f}%</div>
            </div>
          </div>

          <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;color:#E2E8F0'>3. Risk Committee Governance</div>
          <div style='font-family:"Barlow",sans-serif;font-size:14px;color:#B0BAD0;line-height:1.7;margin-bottom:16px'>
          The committee comprises <b>{len(r_comm)} members</b>.
          Average expertise score: <b>{avg_exp:.0f}/100</b> ({expertise_badge(avg_exp)}).
          Risk-certified members: <b>{r_comm["Risk_Management_Certified"].sum()}</b>.
          Board director experienced: <b>{r_comm["Board_Director_Experience"].sum()}</b>.
          </div>

          <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;color:#E2E8F0'>4. Recommendations</div>
          <div style='font-family:"Barlow",sans-serif;font-size:14px;color:#B0BAD0;line-height:1.7'>
          {"⚠ <b>Immediate action required:</b> NPL ratio exceeds the critical threshold. The board should convene an emergency credit risk review, mandate stress testing, and strengthen provisioning." if rd["NPL_Ratio"] >= npl_threshold else "✅ Credit risk indicators are within acceptable bounds. The committee should maintain current monitoring frequency and review sector concentration limits at the next scheduled meeting."}
          {"<br>📌 <b>Governance:</b> Consider recruiting additional CFA/FRM-certified members to strengthen analytical depth of the committee." if avg_exp < 60 else "<br>📌 <b>Governance:</b> Expertise composition is adequate — continue professional development programme."}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Committee members table for report
        st.markdown("**Committee Members — " + r_bank + "**")
        rep_comm = r_comm[["Name","Role","Qualifications","Years_Experience","Expertise_Score"]].copy()
        rep_comm.columns = ["Name","Role","Qualifications","Exp (yrs)","Score"]
        st.dataframe(rep_comm, use_container_width=True, hide_index=True)

        # Download placeholder
        csv = r_comm.to_csv(index=False)
        st.download_button("⬇  Export Committee Data (CSV)", csv,
                           file_name=f"{r_bank.replace(' ','_')}_committee_{r_period}.csv",
                           mime="text/csv")

    # Governance recommendations section
    st.markdown('<div class="section-header">Governance Enhancement Recommendations</div>', unsafe_allow_html=True)
    recs = [
        ("Mandatory Financial Expertise Threshold",
         "RBZ should mandate that at least 60% of risk committee members hold CFA, FRM, CA(Z) or equivalent qualifications.",
         "Regulator / RBZ"),
        ("Structured Onboarding & CPD",
         "Banks should implement continuing professional development programmes covering IFRS 9 expected credit loss, Basel III and sector-specific credit analytics.",
         "Bank Boards"),
        ("Independent Risk Committee Chair",
         "The committee chair should be an independent non-executive director with minimum 10 years' senior banking experience.",
         "Governance Committees"),
        ("Quarterly Credit Risk Reporting",
         "Boards should receive quarterly credit risk dashboards showing NPL trends, sector exposure and provisioning adequacy, with early warning flags.",
         "Risk Management"),
        ("ZAMCO Lessons Integration",
         "Governance frameworks should embed lessons from ZAMCO's NPL resolution, ensuring early identification of distressed assets before systemic accumulation.",
         "All Stakeholders"),
    ]
    for title, desc, owner in recs:
        st.markdown(f"""
        <div class='card'>
          <div style='display:flex;justify-content:space-between;align-items:flex-start'>
            <div style='font-family:"Barlow Condensed",sans-serif;font-size:16px;font-weight:700;color:#E2E8F0'>{title}</div>
            <div style='font-family:"IBM Plex Mono",monospace;font-size:9px;color:#0091FF;text-transform:uppercase;letter-spacing:.08em;border:1px solid #0091FF;border-radius:3px;padding:2px 6px;white-space:nowrap'>{owner}</div>
          </div>
          <div style='font-family:"Barlow",sans-serif;font-size:13px;color:#8A98B8;margin-top:6px'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)
