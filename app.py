"""
RMM Dashboard – Maturity Assessment Dashboard
Aligned with Appendix A (framework) and Appendix B (questionnaire / action plan)
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath('.'))

from src.utils import (
    load_data, get_maturity_level_description, get_maturity_level_name,
    get_maturity_color, get_combined_maturity_quadrant, apply_custom_css, VALID_AREAS,
)
from src.scoring import (
    validate_responses,
    compute_factor_scores,
    compute_area_scores,
    compute_overall_score,
    compute_gap_analysis,
    compute_participation_stats,
)
from src.visuals import (
    create_radar_chart,
    create_maturity_distribution,
    create_heatmap,
    create_org_comparison,
    create_sunburst_chart,
    create_bubble_chart,
    create_proficiency_coverage_chart,
    create_area_proficiency_coverage_chart,
    MATURITY_NAMES,
)

st.set_page_config(
    page_title="RMM Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_custom_css()


def main():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown('<div class="main-header">RMM Maturity Assessment</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Research Management Maturity – '
        'Proficiency &amp; Coverage assessment across PM, EIM, and Invoicing domains</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── Load data ─────────────────────────────────────────────────────────────
    try:
        factors_df, responses_df, actions_df = load_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("Please generate dummy data first by running: `python src/generate_dummy_data.py`")
        return

    responses_df = validate_responses(responses_df, factors_df)

    # ── Sidebar – Global Controls ─────────────────────────────────────────────
    st.sidebar.header("🎛️ Global Controls")

    cycles = sorted(responses_df['cycle_id'].unique())
    selected_cycle = st.sidebar.selectbox(
        "Assessment Cycle", cycles, index=len(cycles) - 1,
        help="Select the assessment cycle to view",
    )

    org_groups = ['All'] + sorted(responses_df['org_group'].unique().tolist())
    selected_org = st.sidebar.selectbox(
        "Organisational Group", org_groups,
        help="Filter by organisational group (Appendix A8)",
    )

    # Areas use Appendix A1 domain names
    areas = ['All'] + VALID_AREAS
    selected_area = st.sidebar.selectbox(
        "Domain (Focus Area)", areas,
        help="Filter by RMM domain: PM (Q7-Q21) | EIM (Q22-Q35) | INV (Q36-Q48)",
    )

    show_evidence_only = st.sidebar.checkbox(
        "Only items with evidence",
        help="Show only factors with supporting documentation",
    )

    st.sidebar.subheader("Confidence Filters")
    min_responses = st.sidebar.slider("Minimum responses", 1, 10, 3,
                                      help="Minimum responses required (quality threshold)")
    max_dispersion = st.sidebar.slider("Maximum disagreement (IQR)", 0.0, 3.0, 2.0,
                                       help="Maximum acceptable inter-rater dispersion")

    # ── Compute scores ────────────────────────────────────────────────────────
    org_filter = None if selected_org == 'All' else selected_org
    factor_scores = compute_factor_scores(responses_df, factors_df, selected_cycle, org_filter)

    if selected_area != 'All':
        factor_scores = factor_scores[factor_scores['area'] == selected_area]
    if show_evidence_only:
        factor_scores = factor_scores[factor_scores['evidence_rate'] > 0]
    factor_scores = factor_scores[
        (factor_scores['n_responses'] >= min_responses) &
        (factor_scores['dispersion'] <= max_dispersion)
    ]

    if len(factor_scores) == 0:
        st.warning("No data matches the selected filters. Please adjust your filter criteria.")
        return

    area_scores  = compute_area_scores(factor_scores)
    overall_score = compute_overall_score(area_scores)
    gaps_df      = compute_gap_analysis(factor_scores, actions_df)
    participation = compute_participation_stats(responses_df, selected_cycle)

    # ── Sidebar – Export ──────────────────────────────────────────────────────
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Export")
    from src.pdf_gen import generate_pdf_report
    if st.sidebar.button("Generate PDF Report"):
        with st.spinner("Generating PDF Report…"):
            pdf_file = generate_pdf_report(overall_score, area_scores, factor_scores, gaps_df, selected_cycle)
            st.sidebar.download_button(
                label="📥 Download PDF",
                data=pdf_file,
                file_name=f"RMM_Report_{selected_cycle}.pdf",
                mime="application/pdf",
            )

    # ── KPI Row 1 – Overall + Domain scores ──────────────────────────────────
    st.subheader("📈 Key Performance Indicators")
    kpi_cols = st.columns(5)

    overall_level = int(overall_score['overall_level'])
    overall_index = overall_score['overall_index']
    overall_prof  = overall_score.get('overall_proficiency', overall_index)
    overall_cov   = overall_score.get('overall_coverage', overall_index)

    with kpi_cols[0]:
        st.metric(
            "Overall Maturity",
            f"{overall_index:.1f} / 5.0",
            f"Level {overall_level} – {MATURITY_NAMES.get(overall_level, '')}",
            help=get_maturity_level_description(overall_level),
        )
        st.markdown(
            f"<div style='color:{get_maturity_color(overall_level)};font-weight:bold;'>"
            f"{get_maturity_level_description(overall_level)}</div>",
            unsafe_allow_html=True,
        )

    # Domain KPIs – Appendix A1 domain names
    domain_kpis = [
        ("Project Management",              "PM"),
        ("Evaluation & Impact Measurement", "EIM"),
        ("Invoicing Process",               "INV"),
    ]
    for col, (domain, abbr) in zip(kpi_cols[1:4], domain_kpis):
        row = area_scores[area_scores['area'] == domain]
        with col:
            if len(row) > 0:
                lvl = int(row['area_level'].values[0])
                idx = float(row['area_index'].values[0])
                st.metric(
                    f"{abbr} – {domain.split(' ')[0]}",
                    f"{idx:.1f} / 5.0",
                    f"Level {lvl} – {MATURITY_NAMES.get(lvl, '')}",
                )

    with kpi_cols[4]:
        st.metric("Priority Gaps", len(gaps_df),
                  help="Number of factors below their target maturity level")

    # KPI Row 2 – Dual-dimension + participation
    kpi_cols2 = st.columns(4)
    with kpi_cols2[0]:
        st.metric("Avg Proficiency", f"{overall_prof:.1f} / 5.0",
                  help="Average proficiency score – how well practices are performed (Appendix A3)")
    with kpi_cols2[1]:
        st.metric("Avg Coverage", f"{overall_cov:.1f} / 5.0",
                  help="Average coverage score – how widely practices are adopted (Appendix A4)")
    with kpi_cols2[2]:
        st.metric("Participation", f"{participation['total_respondents']} respondents",
                  help="Total unique respondents in this cycle")
    with kpi_cols2[3]:
        avg_dispersion = factor_scores['dispersion'].mean()
        st.metric("Avg Disagreement (IQR)", f"{avg_dispersion:.2f}",
                  help="Average inter-rater disagreement (lower = better consensus)")

    # Quadrant callout (Appendix A5)
    if 'overall_proficiency' in overall_score and 'overall_coverage' in overall_score:
        quadrant = get_combined_maturity_quadrant(overall_prof, overall_cov)
        quad_color = "#2ecc71" if "Institutional" in quadrant else (
                     "#3498db" if "Strong" in quadrant else (
                     "#f39c12" if "Widespread" in quadrant else "#e74c3c"))
        st.info(f"🔲 **Combined Maturity Quadrant (Appendix A5):** {quadrant}")

    st.markdown("---")

    # ── Main tabs ─────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Executive Overview",
        "🔬 Proficiency vs Coverage",
        "📋 Factor Details",
        "🎯 Improvement Backlog",
    ])

    # ── Tab 1: Executive Overview ─────────────────────────────────────────────
    with tab1:
        st.subheader("Executive Overview")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Domain View")
            if len(factor_scores) > 0:
                radar_fig = create_radar_chart(factor_scores)
                st.plotly_chart(radar_fig, use_container_width=True)
            sunburst_fig = create_sunburst_chart(factor_scores)
            st.plotly_chart(sunburst_fig, use_container_width=True)

        with col2:
            st.markdown("#### Group Comparison")
            if org_filter is None:
                heatmap_fig = create_heatmap(responses_df, factors_df, selected_cycle)
                st.plotly_chart(heatmap_fig, use_container_width=True)
                org_comp_fig = create_org_comparison(responses_df, factors_df, selected_cycle)
                st.plotly_chart(org_comp_fig, use_container_width=True)
            else:
                st.info("Group comparison available when 'All' organisational groups selected.")

        # Top 10 priority gaps
        st.markdown("#### 🎯 Top 10 Priority Gaps")
        if len(gaps_df) > 0:
            top_gaps = gaps_df.head(10)[[
                'factor_name', 'area', 'current_level', 'target_level',
                'gap_levels', 'transition', 'impact', 'effort',
                'priority_score', 'owner_group', 'timeframe',
            ]].copy()
            top_gaps['priority_score'] = top_gaps['priority_score'].round(2)
            top_gaps.columns = [
                'Factor', 'Domain', 'Current', 'Target',
                'Gap', 'Transition', 'Impact', 'Effort',
                'Priority', 'Owner', 'Timeframe',
            ]
            st.dataframe(top_gaps, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No gaps identified – all factors meet or exceed their targets!")

    # ── Tab 2: Proficiency vs Coverage (Appendix A2-A5) ──────────────────────
    with tab2:
        st.subheader("Proficiency vs Coverage Analysis (Appendix A2–A5)")
        st.markdown(
            "The RMM evaluates maturity using two complementary dimensions. "
            "**Proficiency** measures how well a practice is performed; "
            "**Coverage** measures how widely it is adopted across organisational groups. "
            "True maturity requires both – a well-executed practice confined to one team "
            "does not represent programme-level maturity."
        )

        col1, col2 = st.columns(2)
        with col1:
            pc_fig = create_proficiency_coverage_chart(factor_scores)
            st.plotly_chart(pc_fig, use_container_width=True)
        with col2:
            ac_fig = create_area_proficiency_coverage_chart(area_scores)
            st.plotly_chart(ac_fig, use_container_width=True)

            # Domain-level proficiency/coverage table
            st.markdown("**Domain Proficiency vs Coverage Summary**")
            if 'avg_proficiency' in area_scores.columns:
                pc_table = area_scores[['area', 'avg_proficiency', 'avg_coverage', 'area_index']].copy()
                pc_table.columns = ['Domain', 'Avg Proficiency', 'Avg Coverage', 'Combined Index']
                pc_table = pc_table.round(2)
                st.dataframe(pc_table, use_container_width=True, hide_index=True)

        # Appendix A5 quadrant explanation
        st.markdown("---")
        st.markdown("#### Combined Maturity Quadrants (Appendix A5)")
        q_cols = st.columns(4)
        quadrants = [
            ("🟢 Institutional Maturity", "High Proficiency + High Coverage",
             "Stable programme with consistent, organisation-wide practices.", "#e8faf0"),
            ("🔵 Strong – Not Yet Scaled", "High Proficiency + Low Coverage",
             "Excellent practices exist but adoption is limited to a few groups.", "#e8f0fe"),
            ("🟡 Widespread – Quality Needed", "Low Proficiency + High Coverage",
             "Broad adoption but practice quality needs strengthening.", "#fff8e1"),
            ("🔴 Early Stage", "Low Proficiency + Low Coverage",
             "Ad hoc, person-dependent practices with limited reach.", "#fce8e8"),
        ]
        for col, (label, dims, desc, bg) in zip(q_cols, quadrants):
            with col:
                st.markdown(
                    f"<div style='background:{bg};border-radius:8px;padding:12px;'>"
                    f"<b>{label}</b><br><small>{dims}</small><br>{desc}</div>",
                    unsafe_allow_html=True,
                )

    # ── Tab 3: Factor Details ─────────────────────────────────────────────────
    with tab3:
        st.subheader("Factor Details")

        cols = ['factor_name', 'area', 'median_level', 'target_level',
                'n_responses', 'dispersion', 'evidence_rate', 'index_adjusted']
        if 'proficiency_median' in factor_scores.columns:
            cols += ['proficiency_median', 'coverage_median']

        factor_display = factor_scores[cols].copy()
        factor_display['gap'] = factor_display['target_level'] - factor_display['median_level']
        factor_display['evidence_rate'] = (factor_display['evidence_rate'] * 100).round(1)

        rename_map = {
            'factor_name': 'Factor', 'area': 'Domain',
            'median_level': 'Current Level', 'target_level': 'Target Level',
            'n_responses': 'Responses', 'dispersion': 'Disagreement',
            'evidence_rate': 'Evidence %', 'index_adjusted': 'Index',
            'proficiency_median': 'Proficiency', 'coverage_median': 'Coverage',
            'gap': 'Gap',
        }
        factor_display = factor_display.rename(columns=rename_map)

        def highlight_gaps(row):
            if row.get('Gap', 0) > 0:
                return ['background-color: #ffe6e6'] * len(row)
            return [''] * len(row)

        st.dataframe(
            factor_display.style.apply(highlight_gaps, axis=1),
            use_container_width=True, hide_index=True,
        )

        st.markdown("#### Maturity Level Distribution")
        dist_fig = create_maturity_distribution(factor_scores)
        st.plotly_chart(dist_fig, use_container_width=True)

    # ── Tab 4: Improvement Backlog (Appendix B2) ──────────────────────────────
    with tab4:
        st.subheader("Improvement Backlog (Appendix B2 Action Guidance)")
        st.markdown(
            "Actions are derived from the Appendix B2 action guidance tables and "
            "prioritised by gap severity, expected impact, effort required, and data quality. "
            "Each action is tagged with its level transition (e.g. Level 2 → 3)."
        )

        if len(gaps_df) > 0:
            bl_cols = st.columns(3)
            with bl_cols[0]:
                backlog_area = st.multiselect("Filter by Domain",
                    options=gaps_df['area'].unique(), default=list(gaps_df['area'].unique()))
            with bl_cols[1]:
                backlog_timeframe = st.multiselect("Filter by Timeframe",
                    options=gaps_df['timeframe'].unique(), default=list(gaps_df['timeframe'].unique()))
            with bl_cols[2]:
                backlog_owner = st.multiselect("Filter by Owner",
                    options=gaps_df['owner_group'].unique(), default=list(gaps_df['owner_group'].unique()))

            filtered_gaps = gaps_df[
                gaps_df['area'].isin(backlog_area) &
                gaps_df['timeframe'].isin(backlog_timeframe) &
                gaps_df['owner_group'].isin(backlog_owner)
            ]
            st.markdown(f"**Showing {len(filtered_gaps)} actions**")

            backlog_display = filtered_gaps[[
                'factor_name', 'area', 'action_text', 'transition',
                'current_level', 'target_level', 'gap_levels',
                'impact', 'effort', 'timeframe', 'priority_score', 'owner_group',
            ]].copy()
            backlog_display['priority_score'] = backlog_display['priority_score'].round(2)
            backlog_display.columns = [
                'Factor', 'Domain', 'Action', 'Transition',
                'Current', 'Target', 'Gap',
                'Impact', 'Effort', 'Timeframe', 'Priority', 'Owner',
            ]
            st.dataframe(backlog_display, use_container_width=True, hide_index=True, height=400)

            st.markdown("#### Effort vs Impact Analysis (Appendix B2)")
            bubble_fig = create_bubble_chart(filtered_gaps)
            st.plotly_chart(bubble_fig, use_container_width=True)
        else:
            st.success("✅ No improvement actions needed – all factors meet their targets!")

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f"""<div style='text-align:center;color:#7f8c8d;font-size:0.9rem;'>
        RMM Maturity Assessment Dashboard | TDOT Research &amp; Innovation Office |
        Framework: Appendix A | Questionnaire: Appendix B |
        Data refreshed: {responses_df['timestamp'].max().strftime('%Y-%m-%d')}
        </div>""",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
