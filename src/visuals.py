"""
Visualisation utilities for RMM Dashboard
Aligned with Appendix A: RMM Framework and Assessment Logic
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ── Colour schemes matching Appendix A1 domain colours ───────────────────────
AREA_COLORS = {
    'Project Management':              '#0033A0',   # TDOT Blue
    'Evaluation & Impact Measurement': '#E31837',   # TDOT Red
    'Invoicing Process':               '#708090',   # Slate Gray
}

MATURITY_COLORS = {
    1: '#e74c3c',  # Initial       – Red
    2: '#f39c12',  # Development   – Orange
    3: '#f1c40f',  # Defined       – Yellow
    4: '#3498db',  # Managed       – Blue
    5: '#2ecc71',  # Optimising    – Green
}

# Appendix A6 maturity stage labels
MATURITY_NAMES = {1: 'Initial', 2: 'Development', 3: 'Defined', 4: 'Managed', 5: 'Optimising'}

COMMON_LAYOUT = dict(
    paper_bgcolor='white',
    plot_bgcolor='white',
    font=dict(color='#333333', family="Inter, sans-serif"),
    margin=dict(t=50, l=20, r=20, b=20),
)


# ── Radar chart ───────────────────────────────────────────────────────────────

def create_radar_chart(factor_scores_df):
    """Radar chart of factor maturity across the three RMM domains."""
    fig = go.Figure()
    for area in factor_scores_df['area'].unique():
        area_data = factor_scores_df[factor_scores_df['area'] == area]
        fig.add_trace(go.Scatterpolar(
            r=area_data['index_adjusted'].tolist(),
            theta=area_data['factor_name'].tolist(),
            fill='toself',
            name=area,
            line=dict(color=AREA_COLORS.get(area, '#95a5a6'), width=2),
            marker=dict(size=4),
        ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5],
                            gridcolor='rgba(0,0,0,0.1)', linecolor='rgba(0,0,0,0.1)',
                            tickfont=dict(color='#666666')),
            angularaxis=dict(gridcolor='rgba(0,0,0,0.1)', linecolor='rgba(0,0,0,0.1)',
                             tickfont=dict(color='#333333')),
            bgcolor='white',
        ),
        showlegend=True,
        legend=dict(font=dict(color='#333333')),
        title=dict(text="Factor Maturity by Domain", font=dict(color='#0033A0')),
        height=500,
        **COMMON_LAYOUT,
    )
    return fig


# ── Appendix A5 Proficiency vs Coverage quadrant chart ────────────────────────

def create_proficiency_coverage_chart(factor_scores_df):
    """
    Appendix A5 combined maturity logic: scatter plot of Proficiency vs Coverage.
    Quadrants:
      Top-right   (P≥3, C≥3) → Institutional maturity
      Top-left    (P<3, C≥3) → Widespread adoption needing quality improvement
      Bottom-right (P≥3,C<3) → Strong practices not yet scaled
      Bottom-left  (P<3, C<3)→ Early-stage capability
    """
    if 'proficiency_median' not in factor_scores_df.columns or \
       'coverage_median' not in factor_scores_df.columns:
        fig = go.Figure()
        fig.add_annotation(text="Proficiency/Coverage data not available", showarrow=False)
        return fig

    df = factor_scores_df.dropna(subset=['proficiency_median', 'coverage_median']).copy()

    fig = go.Figure()

    # Quadrant shading
    quadrant_configs = [
        (3, 5, 3, 5, 'rgba(46,204,113,0.08)',  "Institutional Maturity"),
        (0, 3, 3, 5, 'rgba(241,196,15,0.08)',  "Widespread – Quality Needed"),
        (3, 5, 0, 3, 'rgba(52,152,219,0.08)',  "Strong – Not Yet Scaled"),
        (0, 3, 0, 3, 'rgba(231,76,60,0.08)',   "Early Stage"),
    ]
    for x0, x1, y0, y1, color, label in quadrant_configs:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
                      fillcolor=color, line=dict(width=0))
        fig.add_annotation(x=(x0+x1)/2, y=(y0+y1)/2, text=f"<i>{label}</i>",
                           showarrow=False, font=dict(size=10, color='#888888'))

    # Plot factors per area
    for area in df['area'].unique():
        adf = df[df['area'] == area]
        fig.add_trace(go.Scatter(
            x=adf['proficiency_median'].tolist(),
            y=adf['coverage_median'].tolist(),
            mode='markers',
            name=area,
            marker=dict(color=AREA_COLORS.get(area, '#95a5a6'), size=10,
                        line=dict(width=1, color='white')),
            text=adf['factor_name'].tolist(),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Proficiency: %{x:.1f}<br>"
                "Coverage: %{y:.1f}<extra></extra>"
            ),
        ))

    # Dividing lines
    fig.add_hline(y=3, line_dash="dash", line_color="#cccccc", line_width=1)
    fig.add_vline(x=3, line_dash="dash", line_color="#cccccc", line_width=1)

    fig.update_layout(
        title=dict(text="Proficiency vs Coverage (Appendix A5)", font=dict(color='#0033A0')),
        xaxis=dict(title="Proficiency (how well)", range=[0.5, 5.5],
                   tickvals=[1,2,3,4,5],
                   ticktext=[f"{i}<br><span style='font-size:9px'>{MATURITY_NAMES[i]}</span>" for i in range(1,6)],
                   gridcolor='rgba(0,0,0,0.06)', tickfont=dict(color='#333333')),
        yaxis=dict(title="Coverage (how widely)", range=[0.5, 5.5],
                   tickvals=[1,2,3,4,5],
                   ticktext=[f"{i} – {MATURITY_NAMES[i]}" for i in range(1,6)],
                   gridcolor='rgba(0,0,0,0.06)', tickfont=dict(color='#333333')),
        height=500,
        **COMMON_LAYOUT,
    )
    return fig


# ── Domain-level proficiency / coverage bar chart ────────────────────────────

def create_area_proficiency_coverage_chart(area_scores_df):
    """
    Grouped bar chart comparing avg Proficiency vs avg Coverage per domain.
    Visualises the Appendix A2 dual-dimension philosophy at domain level.
    """
    if 'avg_proficiency' not in area_scores_df.columns:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Proficiency',
        x=area_scores_df['area'].tolist(),
        y=area_scores_df['avg_proficiency'].tolist(),
        marker_color='#0033A0',
    ))
    fig.add_trace(go.Bar(
        name='Coverage',
        x=area_scores_df['area'].tolist(),
        y=area_scores_df['avg_coverage'].tolist(),
        marker_color='#E31837',
    ))
    fig.update_layout(
        barmode='group',
        title=dict(text="Proficiency vs Coverage by Domain (Appendix A2)", font=dict(color='#0033A0')),
        yaxis=dict(range=[0, 5.2], title="Score (1–5)", gridcolor='rgba(0,0,0,0.06)',
                   tickfont=dict(color='#333333')),
        xaxis=dict(tickfont=dict(color='#333333')),
        legend=dict(font=dict(color='#333333')),
        height=350,
        **COMMON_LAYOUT,
    )
    return fig


# ── Sunburst chart ────────────────────────────────────────────────────────────

def create_sunburst_chart(factor_scores_df):
    """Hierarchical sunburst: Overall → Domain → Component."""
    ids, parents, values, colors, hover_text = [], [], [], [], []

    ids.append("Total")
    parents.append("")
    values.append(factor_scores_df['index_adjusted'].mean())
    colors.append(factor_scores_df['index_adjusted'].mean())
    hover_text.append(f"Overall: {factor_scores_df['index_adjusted'].mean():.2f}")

    for area in factor_scores_df['area'].unique():
        adf = factor_scores_df[factor_scores_df['area'] == area]
        area_score = adf['index_adjusted'].mean()
        ids.append(area)
        parents.append("Total")
        values.append(area_score)
        colors.append(area_score)
        hover_text.append(f"{area}: {area_score:.2f}")

        for _, row in adf.iterrows():
            ids.append(f"{area} - {row['factor_name']}")
            parents.append(area)
            values.append(row['index_adjusted'])
            colors.append(row['index_adjusted'])
            hover_text.append(f"{row['factor_name']}: {row['index_adjusted']:.2f}")

    fig = go.Figure(go.Sunburst(
        ids=ids,
        labels=[x.split(' - ')[-1] for x in ids],
        parents=parents,
        values=[1] * len(ids),
        marker=dict(colors=colors, colorscale='RdYlBu_r', cmin=1, cmax=5,
                    line=dict(width=0.5, color='white')),
        hovertemplate='<b>%{label}</b><br>Score: %{marker.color:.2f}<extra></extra>',
        branchvalues='total',
    ))
    fig.update_layout(
        title=dict(text="Maturity Hierarchy (Domain → Component)", font=dict(color='#0033A0')),
        height=600, **COMMON_LAYOUT,
    )
    return fig


# ── Maturity level distribution ───────────────────────────────────────────────

def create_maturity_distribution(factor_scores_df):
    distribution = []
    for level in range(1, 6):
        count = ((factor_scores_df['median_level'] >= level - 0.5) &
                 (factor_scores_df['median_level'] <  level + 0.5)).sum()
        distribution.append({'Level': f'Level {level} – {MATURITY_NAMES[level]}', 'Count': int(count)})
    dist_df = pd.DataFrame(distribution)
    fig = px.bar(dist_df, x='Level', y='Count',
                 title='Maturity Level Distribution',
                 color='Level',
                 color_discrete_sequence=[MATURITY_COLORS[i] for i in range(1, 6)])
    fig.update_layout(showlegend=False, height=300,
                      title=dict(text='Maturity Level Distribution', font=dict(color='#0033A0')),
                      xaxis=dict(tickfont=dict(color='#333333')),
                      yaxis=dict(tickfont=dict(color='#333333')))
    return fig


# ── Heatmap ───────────────────────────────────────────────────────────────────

def create_heatmap(responses_df, factors_df, cycle_id):
    """Heatmap of org groups × factors maturity matrix."""
    from src.scoring import compute_factor_scores
    heatmap_data = []
    for org_group in responses_df['org_group'].unique():
        factor_scores = compute_factor_scores(responses_df, factors_df, cycle_id, org_group)
        for _, factor in factor_scores.iterrows():
            fname = factor['factor_name'][:30] + '…' if len(factor['factor_name']) > 30 else factor['factor_name']
            heatmap_data.append({'Org Group': org_group, 'Factor': fname,
                                 'Maturity Index': factor['index_adjusted']})
    heatmap_df = pd.DataFrame(heatmap_data)
    pivot = heatmap_df.pivot(index='Org Group', columns='Factor', values='Maturity Index')
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values.tolist(), x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale='RdYlBu_r', zmid=3, zmin=1, zmax=5,
        colorbar=dict(title=dict(text="Maturity", font=dict(color='#333333')),
                      tickfont=dict(color='#333333')),
    ))
    fig.update_layout(
        title=dict(text='Maturity Heatmap: Org Groups × Factors', font=dict(color='#0033A0')),
        xaxis_title='Factors', yaxis_title='Organisational Groups',
        height=400,
        xaxis=dict(tickangle=-45, tickfont=dict(color='#333333')),
        yaxis=dict(tickfont=dict(color='#333333')),
        **COMMON_LAYOUT,
    )
    return fig


# ── Org comparison dot plot ───────────────────────────────────────────────────

def create_org_comparison(responses_df, factors_df, cycle_id):
    """Dot plot of overall maturity by org group with disagreement error bars."""
    from src.scoring import compute_factor_scores, compute_overall_score, compute_area_scores
    comparison_data = []
    for org_group in responses_df[responses_df['cycle_id'] == cycle_id]['org_group'].unique():
        fs = compute_factor_scores(responses_df, factors_df, cycle_id, org_group)
        overall = compute_overall_score(compute_area_scores(fs))
        comparison_data.append({
            'Org Group': org_group,
            'Overall Index': overall['overall_index'],
            'Disagreement': float(fs['index_adjusted'].std()),
        })
    comp_df = pd.DataFrame(comparison_data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=comp_df['Overall Index'].tolist(), y=comp_df['Org Group'].tolist(),
        error_x=dict(type='data', array=comp_df['Disagreement'].tolist(), visible=True, color='#0033A0'),
        mode='markers',
        marker=dict(size=12, color='#0033A0'),
        name='Maturity Index',
    ))
    fig.update_layout(
        title=dict(text='Overall Maturity by Org Group (Appendix A8)', font=dict(color='#0033A0')),
        xaxis_title='Overall Maturity Index', yaxis_title='Organisational Group',
        height=300,
        xaxis=dict(range=[1, 5], tickfont=dict(color='#333333'), gridcolor='rgba(0,0,0,0.1)'),
        yaxis=dict(tickfont=dict(color='#333333'), gridcolor='rgba(0,0,0,0.1)'),
        **COMMON_LAYOUT,
    )
    return fig


# ── Bubble chart (improvement backlog) ───────────────────────────────────────

def create_bubble_chart(gaps_df):
    """Effort vs Impact bubble chart for the Appendix B2 improvement backlog."""
    if len(gaps_df) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No gaps identified", showarrow=False)
        return fig
    fig = px.scatter(
        gaps_df.head(50), x='effort', y='impact', size='gap_levels',
        color='area', hover_data=['factor_name', 'action_text', 'priority_score', 'transition'],
        title='Improvement Actions: Effort vs Impact (Appendix B2)',
        labels={'effort': 'Effort Required', 'impact': 'Expected Impact'},
        color_discrete_map=AREA_COLORS, size_max=30,
    )
    # Highlight quick-wins quadrant
    fig.add_shape(type="rect", x0=0.5, x1=2.5, y0=3.5, y1=5.5,
                  fillcolor="rgba(46,204,113,0.08)", line=dict(color="#2ecc71", dash="dot"))
    fig.add_annotation(x=1.5, y=5.3, text="Quick Wins ↗", showarrow=False,
                       font=dict(size=10, color='#2ecc71'))
    fig.update_layout(
        title=dict(text='Improvement Actions: Effort vs Impact (Appendix B2)', font=dict(color='#0033A0')),
        height=500,
        xaxis=dict(gridcolor='rgba(0,0,0,0.1)', tickfont=dict(color='#333333')),
        yaxis=dict(gridcolor='rgba(0,0,0,0.1)', tickfont=dict(color='#333333')),
        legend=dict(font=dict(color='#333333')),
        **COMMON_LAYOUT,
    )
    return fig


# ── Trend charts ──────────────────────────────────────────────────────────────

def create_trend_line(trend_df, metric_col, title):
    """Filled area chart for overall maturity trend."""
    fig = px.area(trend_df, x='cycle_id', y=metric_col, title=title,
                  markers=True, line_shape='spline')
    fig.update_traces(line_color='#0033A0', fillcolor='rgba(0,51,160,0.15)')
    fig.update_layout(
        title=dict(text=title, font=dict(color='#0033A0')),
        xaxis_title='Assessment Cycle', yaxis_title='Maturity Index (1–5)',
        height=350,
        xaxis=dict(gridcolor='rgba(0,0,0,0.06)', tickfont=dict(color='#333333')),
        yaxis=dict(gridcolor='rgba(0,0,0,0.06)', tickfont=dict(color='#333333'), range=[0, 5.5]),
        **COMMON_LAYOUT,
    )
    return fig


def create_area_trends(trend_df):
    """Line chart of maturity trends by RMM domain."""
    fig = px.line(trend_df, x='cycle_id', y='area_index', color='area',
                  title='Maturity Trends by Domain', markers=True,
                  color_discrete_map=AREA_COLORS)
    fig.update_layout(
        title=dict(text='Maturity Trends by Domain (PM / EIM / INV)', font=dict(color='#0033A0')),
        xaxis_title='Assessment Cycle', yaxis_title='Domain Maturity Index',
        height=400,
        xaxis=dict(gridcolor='rgba(0,0,0,0.06)', tickfont=dict(color='#333333')),
        yaxis=dict(gridcolor='rgba(0,0,0,0.06)', tickfont=dict(color='#333333')),
        legend=dict(font=dict(color='#333333')),
        **COMMON_LAYOUT,
    )
    return fig


def create_slope_chart(trend_df):
    """Slope chart comparing baseline vs latest factor maturity."""
    cycles = trend_df['cycle_id'].unique()
    if len(cycles) < 2:
        fig = go.Figure()
        fig.add_annotation(text="Need at least 2 cycles for comparison", showarrow=False)
        return fig
    baseline, latest = cycles[0], cycles[-1]
    bl = trend_df[trend_df['cycle_id'] == baseline]
    lt = trend_df[trend_df['cycle_id'] == latest]
    merged = bl.merge(lt, on=['factor_id', 'factor_name'], suffixes=('_baseline', '_latest'))
    fig = go.Figure()
    for _, row in merged.iterrows():
        change = row['index_adjusted_latest'] - row['index_adjusted_baseline']
        color  = '#2ecc71' if change > 0 else ('#e74c3c' if change < 0 else '#95a5a6')
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[row['index_adjusted_baseline'], row['index_adjusted_latest']],
            mode='lines+markers', name=row['factor_name'],
            line=dict(width=2, color=color), marker=dict(size=8),
        ))
    fig.update_layout(
        title=dict(text=f'Factor Changes: {baseline} → {latest}', font=dict(color='#0033A0')),
        xaxis=dict(tickmode='array', tickvals=[0, 1], ticktext=[baseline, latest],
                   tickfont=dict(color='#333333', size=14), gridcolor='rgba(0,0,0,0.06)'),
        yaxis=dict(title='Maturity Index', gridcolor='rgba(0,0,0,0.06)', tickfont=dict(color='#333333')),
        height=600, showlegend=True, legend=dict(font=dict(color='#333333')),
        **COMMON_LAYOUT,
    )
    return fig


# ── Data quality charts ───────────────────────────────────────────────────────

def create_missingness_chart(factor_scores_df):
    """Horizontal bar chart of response coverage by factor."""
    df = factor_scores_df.copy()
    df['response_rate'] = df['n_responses'] / df['n_responses'].max() * 100
    df = df.sort_values('response_rate')
    fig = px.bar(df, x='response_rate', y='factor_name', orientation='h',
                 title='Response Coverage by Factor',
                 labels={'response_rate': 'Response Rate (%)', 'factor_name': 'Factor'},
                 color='response_rate', color_continuous_scale='RdYlBu_r')
    fig.update_layout(height=600,
                      title=dict(font=dict(color='#0033A0')),
                      xaxis=dict(tickfont=dict(color='#333333'), gridcolor='rgba(0,0,0,0.06)'),
                      yaxis=dict(tickfont=dict(color='#333333')))
    return fig


def create_evidence_coverage(factor_scores_df):
    """Horizontal bar of evidence coverage for factors that require it."""
    df = factor_scores_df[factor_scores_df['evidence_required'] == 1].copy()
    df['evidence_pct'] = df['evidence_rate'] * 100
    df = df.sort_values('evidence_pct')
    fig = px.bar(df, x='evidence_pct', y='factor_name', orientation='h',
                 title='Evidence Coverage (Required Factors Only)',
                 labels={'evidence_pct': 'Evidence Rate (%)', 'factor_name': 'Factor'},
                 color='evidence_pct', color_continuous_scale='RdYlBu_r')
    fig.update_layout(height=600,
                      title=dict(font=dict(color='#0033A0')),
                      xaxis=dict(tickfont=dict(color='#333333'), gridcolor='rgba(0,0,0,0.06)'),
                      yaxis=dict(tickfont=dict(color='#333333')))
    return fig
