"""
Data Quality & Audit Page
"""
import streamlit as st
import sys
sys.path.insert(0, '.')

from src.utils import load_data, apply_custom_css
from src.scoring import compute_factor_scores, validate_responses
from src.visuals import create_missingness_chart, create_evidence_coverage
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Data Quality & Audit", page_icon="🔍", layout="wide")
apply_custom_css()

st.markdown('<div class="main-header">🔍 Data Quality & Audit</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Assess the reliability and completeness of assessment data</div>', unsafe_allow_html=True)

# Load data
factors_df, responses_df, actions_df = load_data()
responses_df = validate_responses(responses_df, factors_df)

# Sidebar - cycle selector
cycles = sorted(responses_df['cycle_id'].unique())
selected_cycle = st.sidebar.selectbox("Assessment Cycle", cycles, index=len(cycles)-1)

# Compute scores for selected cycle
factor_scores = compute_factor_scores(responses_df, factors_df, selected_cycle)

# Overall data quality score
st.subheader("📊 Overall Data Quality Score")

col1, col2, col3, col4 = st.columns(4)

with col1:
    # Response coverage
    avg_responses = factor_scores['n_responses'].mean()
    response_score = min(100, (avg_responses / 5) * 100)
    st.metric("Response Coverage", f"{response_score:.0f}%", f"{avg_responses:.1f} avg responses")

with col2:
    # Agreement/consensus
    avg_dispersion = factor_scores['dispersion'].mean()
    consensus_score = max(0, 100 - (avg_dispersion / 2 * 100))
    st.metric("Consensus Score", f"{consensus_score:.0f}%", f"{avg_dispersion:.2f} avg IQR")

with col3:
    # Evidence completeness
    evidence_required = factor_scores[factor_scores['evidence_required'] == 1]
    if len(evidence_required) > 0:
        evidence_score = evidence_required['evidence_rate'].mean() * 100
        st.metric("Evidence Completeness", f"{evidence_score:.1f}%")
    else:
        st.metric("Evidence Completeness", "N/A", help="No factors require evidence")

with col4:
    # Overall quality
    overall_quality = (response_score + consensus_score + (evidence_score if len(evidence_required) > 0 else 100)) / 3
    st.metric("Overall Quality", f"{overall_quality:.0f}%")

st.markdown("---")

# Response coverage analysis
st.subheader("📋 Response Coverage Analysis")

col1, col2 = st.columns([2, 1])

with col1:
    # Missingness chart
    missing_fig = create_missingness_chart(factor_scores)
    st.plotly_chart(missing_fig, use_container_width=True)

with col2:
    st.markdown("#### Coverage Statistics")
    
    # Factors by response count
    low_response = len(factor_scores[factor_scores['n_responses'] < 3])
    medium_response = len(factor_scores[(factor_scores['n_responses'] >= 3) & (factor_scores['n_responses'] < 5)])
    high_response = len(factor_scores[factor_scores['n_responses'] >= 5])
    
    st.markdown(f"🔴 **Low coverage** (<3 responses): {low_response} factors")
    st.markdown(f"🟡 **Medium coverage** (3-4 responses): {medium_response} factors")
    st.markdown(f"🟢 **High coverage** (≥5 responses): {high_response} factors")
    
    if low_response > 0:
        st.warning(f"⚠️ {low_response} factor(s) need more responses for reliable assessment")

st.markdown("---")

# Evidence coverage
st.subheader("📎 Evidence & Documentation Coverage")

evidence_required_factors = factor_scores[factor_scores['evidence_required'] == 1]

if len(evidence_required_factors) > 0:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        evidence_fig = create_evidence_coverage(factor_scores)
        st.plotly_chart(evidence_fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Evidence Statistics")
        
        no_evidence = len(evidence_required_factors[evidence_required_factors['evidence_rate'] == 0])
        partial_evidence = len(evidence_required_factors[(evidence_required_factors['evidence_rate'] > 0) & (evidence_required_factors['evidence_rate'] < 0.5)])
        good_evidence = len(evidence_required_factors[evidence_required_factors['evidence_rate'] >= 0.5])
        
        st.markdown(f"🔴 **No evidence**: {no_evidence} factors")
        st.markdown(f"🟡 **Partial evidence** (<50%): {partial_evidence} factors")
        st.markdown(f"🟢 **Good evidence** (≥50%): {good_evidence} factors")
        
        if no_evidence > 0:
            st.warning(f"⚠️ {no_evidence} required factor(s) missing evidence documentation")
else:
    st.info("No factors in this assessment require evidence documentation.")

st.markdown("---")

# Response bias and participation
st.subheader("👥 Participation & Response Bias")

cycle_data = responses_df[responses_df['cycle_id'] == selected_cycle]

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Responses by Organizational Group")
    
    # Count responses by org group
    org_response = cycle_data.groupby('org_group').agg({
        'respondent_id': 'nunique',
        'factor_id': 'count'
    }).rename(columns={'respondent_id': 'Unique Respondents', 'factor_id': 'Total Responses'})
    
    st.dataframe(org_response, use_container_width=True)
    
    # Visualization
    org_fig = px.bar(
        org_response.reset_index(),
        x='org_group',
        y='Total Responses',
        title='Response Distribution by Org Group',
        color='Total Responses',
        color_continuous_scale='Blues'
    )
    st.plotly_chart(org_fig, use_container_width=True)

with col2:
    st.markdown("#### Disagreement Analysis")
    
    # Factors with high disagreement
    high_disagreement = factor_scores[factor_scores['dispersion'] > 1.5].sort_values('dispersion', ascending=False)
    
    if len(high_disagreement) > 0:
        st.markdown(f"**{len(high_disagreement)} factors** have high disagreement (IQR > 1.5)")
        
        st.markdown("**Top 5 Most Contested Factors:**")
        for idx, row in high_disagreement.head(5).iterrows():
            st.markdown(f"- {row['factor_name']}: IQR = {row['dispersion']:.2f}")
    else:
        st.success("✅ No factors show high disagreement")
    
    # Consensus distribution
    consensus_fig = px.histogram(
        factor_scores,
        x='dispersion',
        nbins=20,
        title='Distribution of Disagreement Scores',
        labels={'dispersion': 'Disagreement (IQR)', 'count': 'Number of Factors'}
    )
    st.plotly_chart(consensus_fig, use_container_width=True)

st.markdown("---")

# Confidence analysis
st.subheader("🎯 Confidence Levels")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Average Confidence by Factor")
    
    # Filter factors with confidence data
    with_confidence = factor_scores[factor_scores['confidence_avg'].notna()].copy()
    with_confidence = with_confidence.sort_values('confidence_avg')
    
    if len(with_confidence) > 0:
        conf_fig = px.bar(
            with_confidence.head(15),
            x='confidence_avg',
            y='factor_name',
            orientation='h',
            title='Lowest Confidence Factors (Bottom 15)',
            labels={'confidence_avg': 'Avg Confidence (1-5)', 'factor_name': 'Factor'},
            color='confidence_avg',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(conf_fig, use_container_width=True)
    else:
        st.info("Confidence data not available for this cycle")

with col2:
    st.markdown("#### Confidence Distribution")
    
    if len(with_confidence) > 0:
        conf_dist = px.histogram(
            with_confidence,
            x='confidence_avg',
            nbins=10,
            title='Distribution of Confidence Scores',
            labels={'confidence_avg': 'Average Confidence', 'count': 'Number of Factors'}
        )
        st.plotly_chart(conf_dist, use_container_width=True)
        
        avg_confidence = with_confidence['confidence_avg'].mean()
        st.metric("Average Confidence", f"{avg_confidence:.2f} / 5.0")
    else:
        st.info("Confidence data not available for this cycle")

st.markdown("---")

# Data quality recommendations
st.subheader("💡 Data Quality Recommendations")

recommendations = []

# Check response coverage
if low_response > 5:
    recommendations.append("📌 **Increase participation**: {} factors have fewer than 3 responses. Consider targeted outreach to specific teams.".format(low_response))

# Check evidence
if len(evidence_required_factors) > 0 and no_evidence > 3:
    recommendations.append("📌 **Improve documentation**: {} required factors lack supporting evidence. Set up a documentation checklist.".format(no_evidence))

# Check disagreement
if len(high_disagreement) > 5:
    recommendations.append("📌 **Resolve disagreements**: {} factors show high disagreement. Consider facilitated discussions or clearer assessment criteria.".format(len(high_disagreement)))

# Check org balance
org_counts = cycle_data.groupby('org_group')['respondent_id'].nunique()
if org_counts.max() > org_counts.min() * 3:
    recommendations.append("📌 **Balance participation**: Response rates vary significantly across organizational groups. Ensure all groups are engaged.")

if recommendations:
    for rec in recommendations:
        st.markdown(rec)
else:
    st.success("✅ Data quality is good! No major issues detected.")

st.markdown("---")

# Change log (placeholder)
st.subheader("📝 Change Log")
st.info("Change log tracking for assessment configuration will be available in future versions.")

st.markdown("---")
st.caption("💡 Tip: Regular data quality audits ensure reliable maturity assessments and meaningful trend analysis.")
