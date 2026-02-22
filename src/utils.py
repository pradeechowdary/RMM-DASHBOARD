"""
Utility functions for RMM Dashboard
Aligned with Appendix A maturity level definitions
"""
import pandas as pd
import streamlit as st
from datetime import datetime

# ── Valid area names (must match Appendix A1 domain labels) ──────────────────
VALID_AREAS = [
    "Project Management",
    "Evaluation & Impact Measurement",
    "Invoicing Process",
]

# ── Maturity level definitions (Appendix A3 Proficiency scale + A6 stages) ───
MATURITY_LEVEL_NAMES = {
    1: "Initial",
    2: "Development",
    3: "Defined",
    4: "Managed",
    5: "Optimising",
}

MATURITY_LEVEL_DESCRIPTIONS = {
    1: "Initial – Inconsistent practices and limited adoption; processes are ad hoc and person-dependent",
    2: "Development – Emerging structure with partial organisational use; basic processes exist but are inconsistent",
    3: "Defined – Standardised practices used across multiple groups; documented processes broadly followed",
    4: "Managed – Performance-driven processes widely adopted; quantitative objectives tracked and decisions data-driven",
    5: "Optimising – Organisation-wide continuous improvement and learning; improvement mechanisms are embedded",
}

PROFICIENCY_DESCRIPTIONS = {
    1: "Practices are ad hoc and dependent on individuals",
    2: "Partial structure exists but remains inconsistent",
    3: "Standardised and documented processes are established",
    4: "Performance is measured and used for decision-making",
    5: "Continuous improvement mechanisms are embedded",
}

COVERAGE_DESCRIPTIONS = {
    1: "Isolated or individual use only",
    2: "Limited adoption among few groups",
    3: "Implementation across several groups",
    4: "Broad organisational adoption",
    5: "Organisation-wide, institutionalised use",
}

# ── Area colours matching config.yaml ────────────────────────────────────────
AREA_COLORS = {
    "Project Management":             "#0033A0",
    "Evaluation & Impact Measurement": "#E31837",
    "Invoicing Process":              "#708090",
}

LEVEL_COLORS = {
    1: "#e74c3c",
    2: "#f39c12",
    3: "#f1c40f",
    4: "#3498db",
    5: "#2ecc71",
}


@st.cache_data
def load_data():
    """Load all CSV data files."""
    try:
        factors   = pd.read_csv('data/factors.csv')
        responses = pd.read_csv('data/responses.csv')
        actions   = pd.read_csv('data/actions.csv')
        responses['timestamp'] = pd.to_datetime(responses['timestamp'])
        return factors, responses, actions
    except FileNotFoundError as e:
        st.error(f"Data files not found: {e}")
        st.info("Please run: python src/generate_dummy_data.py")
        st.stop()


def get_maturity_level_name(level: int) -> str:
    return MATURITY_LEVEL_NAMES.get(int(level), "Unknown")


def get_maturity_level_description(level: int) -> str:
    return MATURITY_LEVEL_DESCRIPTIONS.get(int(level), "Unknown level")


def get_proficiency_description(level: int) -> str:
    return PROFICIENCY_DESCRIPTIONS.get(int(level), "")


def get_coverage_description(level: int) -> str:
    return COVERAGE_DESCRIPTIONS.get(int(level), "")


def get_maturity_color(level: int) -> str:
    return LEVEL_COLORS.get(int(level), "#95a5a6")


def get_area_color(area: str) -> str:
    return AREA_COLORS.get(area, "#95a5a6")


def get_combined_maturity_quadrant(proficiency: float, coverage: float) -> str:
    """
    Appendix A5 combined maturity logic:
    - Low proficiency, Low coverage  → Early-stage capability requiring structural improvements
    - High proficiency, Low coverage → Strong practices that have not yet scaled across the organisation
    - Low proficiency, High coverage → Widespread implementation requiring quality improvement
    - High proficiency, High coverage → Institutional maturity and stable programme
    """
    p_high = proficiency >= 3
    c_high = coverage >= 3
    if p_high and c_high:
        return "Institutional maturity and stable programme"
    elif p_high and not c_high:
        return "Strong practices not yet scaled across the organisation"
    elif not p_high and c_high:
        return "Widespread implementation requiring quality improvement"
    else:
        return "Early-stage capability requiring structural improvements"


def get_timeframe_badge(timeframe: str) -> str:
    badges = {'short': '🟢', 'medium': '🟡', 'long': '🔴'}
    return badges.get(timeframe, '⚪')


def calculate_completion_percentage(factor_scores_df) -> float:
    total_possible = len(factor_scores_df) * 10
    actual         = factor_scores_df['n_responses'].sum()
    return min(100.0, (actual / total_possible) * 100)


def export_to_csv(data, filename):
    return data.to_csv(index=False)


def apply_custom_css():
    """Apply TDOT light-theme CSS (blue #0033A0 / red #E31837)."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    :root {
        --tdot-blue:   #0033A0;
        --tdot-red:    #E31837;
        --bg-color:    #F8F9FA;
        --card-bg:     #FFFFFF;
        --text-color:  #333333;
        --text-muted:  #666666;
        --border-color:#E0E0E0;
    }
    html, body{ font-family: 'Inter', sans-serif; color: var(--text-color); background-color: var(--bg-color); }
    .stApp { background-color: var(--bg-color); background-image: none; }
    .main-header {
        color: var(--tdot-blue); font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem;
        text-transform: uppercase; border-bottom: 4px solid var(--tdot-red);
        padding-bottom: 10px; display: inline-block;
    }
    .sub-header { font-size: 1.1rem; color: var(--text-muted); margin-bottom: 2rem; font-weight: 400; }
    hr { margin-top: 1rem; margin-bottom: 1rem; border: 0; border-top: 1px solid var(--border-color); }
    div[data-testid="stMetric"] {
        background: var(--card-bg); border: 1px solid var(--border-color);
        padding: 1rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700; color: var(--tdot-blue); }
    div[data-testid="stMetricLabel"] { font-size: 0.9rem !important; color: var(--text-muted); font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 2px solid var(--border-color); }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent; border: none; color: var(--text-muted); font-weight: 600; padding: 0 20px; }
    .stTabs [aria-selected="true"] { color: var(--tdot-blue); border-bottom: 3px solid var(--tdot-blue); }
    div[data-testid="stDataFrame"] { border: 1px solid var(--border-color); border-radius: 4px; background-color: var(--card-bg); }
    section[data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid var(--border-color); }
    h1, h2, h3 { color: var(--tdot-blue); }
    .dimension-badge {
        display: inline-block; padding: 4px 10px; border-radius: 12px;
        font-size: 0.8rem; font-weight: 600; margin: 2px;
    }
    .proficiency-badge { background-color: #e8f0fe; color: #0033A0; }
    .coverage-badge    { background-color: #fce8e8; color: #E31837; }
</style>
""", unsafe_allow_html=True)
