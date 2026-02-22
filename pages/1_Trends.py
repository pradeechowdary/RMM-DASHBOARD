"""
Trends & Reassessments Page
"""
import streamlit as st
import sys
sys.path.insert(0, '.')

from src.utils import load_data, apply_custom_css
from src.scoring import compute_trend_data, validate_responses
from src.visuals import create_trend_line, create_area_trends, create_slope_chart

st.set_page_config(page_title="Trends & Reassessments", page_icon="📈", layout="wide")
apply_custom_css()

st.markdown('<div class="main-header">📈 Trends & Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Track maturity evolution across assessment cycles</div>', unsafe_allow_html=True)

# Load data
factors_df, responses_df, actions_df = load_data()
responses_df = validate_responses(responses_df, factors_df)

# Check if multiple cycles exist
cycles = sorted(responses_df['cycle_id'].unique())
if len(cycles) < 2:
    st.warning("⚠️ Trend analysis requires at least 2 assessment cycles. Currently only {} cycle(s) available.".format(len(cycles)))
    st.info("The system will track changes once you conduct reassessments.")
    st.stop()

# Compute trend data
st.info("Computing trend data across {} cycles...".format(len(cycles)))
trend_data = compute_trend_data(responses_df, factors_df, actions_df)

# Overall maturity trend
st.subheader("Overall Maturity Trend")
col1, col2 = st.columns([2, 1])

with col1:
    overall_trend_fig = create_trend_line(
        trend_data['overall'],
        'overall_index',
        'Overall Maturity Over Time'
    )
    st.plotly_chart(overall_trend_fig, use_container_width=True)

with col2:
    st.markdown("#### Key Insights")
    
    baseline_score = trend_data['overall'].iloc[0]['overall_index']
    latest_score = trend_data['overall'].iloc[-1]['overall_index']
    change = latest_score - baseline_score
    
    st.metric(
        "Total Change",
        f"{change:+.1f} points",
        delta=f"{(change/baseline_score*100):+.1f}%"
    )
    
    st.metric("Baseline Score", f"{baseline_score:.1f}")
    st.metric("Latest Score", f"{latest_score:.1f}")

st.markdown("---")

# Area trends
st.subheader("Maturity Trends by Area")
area_trend_fig = create_area_trends(trend_data['by_area'])
st.plotly_chart(area_trend_fig, use_container_width=True)

# Area-specific metrics
st.markdown("#### Area Performance Summary")
area_cols = st.columns(3)

for idx, area in enumerate(['Project Management', 'Evaluation & Impact', 'Invoicing']):
    area_data = trend_data['by_area'][trend_data['by_area']['area'] == area]
    
    if len(area_data) > 0:
        baseline = area_data.iloc[0]['area_index']
        latest = area_data.iloc[-1]['area_index']
        change = latest - baseline
        
        with area_cols[idx]:
            st.markdown(f"**{area}**")
            st.metric("Change", f"{change:+.1f}", delta=f"{(change/baseline*100):+.1f}%")
            st.caption(f"From {baseline:.1f} to {latest:.1f}")

st.markdown("---")

# Factor-level slope chart
st.subheader("Factor Changes: Baseline vs Latest")
st.markdown("This chart shows how individual factors have evolved from the baseline to the most recent assessment.")

if len(trend_data['by_factor']) > 0:
    slope_fig = create_slope_chart(trend_data['by_factor'])
    st.plotly_chart(slope_fig, use_container_width=True)
else:
    st.info("Factor-level trend data not available for display.")

st.markdown("---")

# Cycle comparison table
st.subheader("Cycle-by-Cycle Comparison")

comparison_data = []
for cycle in cycles:
    cycle_overall = trend_data['overall'][trend_data['overall']['cycle_id'] == cycle]
    
    if len(cycle_overall) > 0:
        comparison_data.append({
            'Cycle': cycle,
            'Overall Index': cycle_overall.iloc[0]['overall_index'],
            'Overall Level': int(cycle_overall.iloc[0]['overall_level'])
        })

import pandas as pd
comparison_df = pd.DataFrame(comparison_data)

st.dataframe(comparison_df, use_container_width=True, hide_index=True)

# Insights and recommendations
st.markdown("---")
st.subheader("📊 Trend Analysis Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Positive Trends")
    # Identify improving areas
    improving = []
    for area in trend_data['by_area']['area'].unique():
        area_data = trend_data['by_area'][trend_data['by_area']['area'] == area]
        if len(area_data) >= 2:
            baseline = area_data.iloc[0]['area_index']
            latest = area_data.iloc[-1]['area_index']
            if latest > baseline:
                improving.append(f"✅ {area}: +{(latest-baseline):.1f} points")
    
    if improving:
        for item in improving:
            st.markdown(item)
    else:
        st.markdown("No areas showing improvement yet.")

with col2:
    st.markdown("#### Areas Needing Attention")
    # Identify declining or stagnant areas
    declining = []
    for area in trend_data['by_area']['area'].unique():
        area_data = trend_data['by_area'][trend_data['by_area']['area'] == area]
        if len(area_data) >= 2:
            baseline = area_data.iloc[0]['area_index']
            latest = area_data.iloc[-1]['area_index']
            if latest <= baseline:
                declining.append(f"⚠️ {area}: {(latest-baseline):+.1f} points")
    
    if declining:
        for item in declining:
            st.markdown(item)
    else:
        st.markdown("All areas showing improvement!")

st.markdown("---")
st.caption("💡 Tip: Regular reassessments (every 6 months) provide the best trend insights for continuous improvement.")
