"""
Scoring pipeline for RMM Maturity Assessment Dashboard
Implements the dual Proficiency / Coverage model from Appendix A2-A5
"""
import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_responses(responses_df, factors_df):
    """Filter out invalid factor IDs and out-of-range level values."""
    valid_factors = factors_df['factor_id'].unique()
    responses_df = responses_df[responses_df['factor_id'].isin(valid_factors)]
    responses_df = responses_df[responses_df['level'].between(1, 5)]
    # Validate optional columns if they exist
    if 'proficiency_level' in responses_df.columns:
        responses_df = responses_df[responses_df['proficiency_level'].between(1, 5)]
    if 'coverage_level' in responses_df.columns:
        responses_df = responses_df[responses_df['coverage_level'].between(1, 5)]
    return responses_df.copy()


# ─────────────────────────────────────────────────────────────────────────────
# Factor-level scoring (Appendix A7)
# ─────────────────────────────────────────────────────────────────────────────

def compute_factor_scores(responses_df, factors_df, cycle_id, org_group_filter=None):
    """
    Compute per-factor scores including the Appendix A2-A5 dual dimensions:
      - proficiency_median  : median of proficiency_level responses (how well)
      - coverage_median     : median of coverage_level responses (how widely)
      - median_level        : combined maturity (min of proficiency/coverage per Appendix A5)
      - index_adjusted      : 1-5 maturity index after quality penalties
    Quality penalties (Appendix A7):
      -0.5 if n_responses < 3   (low participation)
      -0.5 if IQR > 1.5         (high disagreement)
      -0.5 if evidence_rate < 0.5 (missing required evidence)
    """
    cycle_data = responses_df[responses_df['cycle_id'] == cycle_id].copy()
    if org_group_filter and org_group_filter != 'All':
        cycle_data = cycle_data[cycle_data['org_group'] == org_group_filter]

    factor_scores = []
    has_prof = 'proficiency_level' in cycle_data.columns
    has_cov  = 'coverage_level'    in cycle_data.columns

    for factor_id in factors_df['factor_id']:
        factor_info      = factors_df[factors_df['factor_id'] == factor_id].iloc[0]
        factor_responses = cycle_data[cycle_data['factor_id'] == factor_id]

        if len(factor_responses) == 0:
            factor_scores.append({
                'factor_id':          factor_id,
                'median_level':       np.nan,
                'mean_level':         np.nan,
                'proficiency_median': np.nan,
                'coverage_median':    np.nan,
                'n_responses':        0,
                'dispersion':         np.nan,
                'confidence_avg':     np.nan,
                'evidence_rate':      0.0,
                'index_raw':          1.0,
                'quality_penalty':    0.0,
                'index_adjusted':     1.0,
            })
            continue

        levels = factor_responses['level'].values
        median_level = float(np.median(levels))
        mean_level   = float(np.mean(levels))
        n_responses  = len(levels)
        q75, q25     = np.percentile(levels, [75, 25])
        dispersion   = float(q75 - q25)

        # Dual dimensions (Appendix A3-A4)
        if has_prof:
            proficiency_median = float(np.median(factor_responses['proficiency_level']))
        else:
            proficiency_median = median_level

        if has_cov:
            coverage_median = float(np.median(factor_responses['coverage_level']))
        else:
            coverage_median = median_level

        # Confidence
        if 'confidence' in factor_responses.columns:
            confidence_avg = float(factor_responses['confidence'].mean())
        else:
            confidence_avg = 3.5

        # Evidence rate
        if factor_info['evidence_required']:
            evidence_rate = float(factor_responses['evidence_link'].notna().sum() / n_responses)
        else:
            evidence_rate = 1.0

        # Raw index = combined maturity level (1-5 scale, no transformation needed)
        index_raw = median_level

        # Quality penalties (Appendix A7)
        quality_penalty = 0.0
        if n_responses < 3:
            quality_penalty += 0.5
        if dispersion > 1.5:
            quality_penalty += 0.5
        if factor_info['evidence_required'] and evidence_rate < 0.5:
            quality_penalty += 0.5

        index_adjusted = max(1.0, index_raw - quality_penalty)

        factor_scores.append({
            'factor_id':          factor_id,
            'median_level':       median_level,
            'mean_level':         mean_level,
            'proficiency_median': proficiency_median,
            'coverage_median':    coverage_median,
            'n_responses':        n_responses,
            'dispersion':         dispersion,
            'confidence_avg':     confidence_avg,
            'evidence_rate':      evidence_rate,
            'index_raw':          index_raw,
            'quality_penalty':    quality_penalty,
            'index_adjusted':     index_adjusted,
        })

    scores_df = pd.DataFrame(factor_scores)
    scores_df  = scores_df.merge(factors_df, on='factor_id', how='left')
    return scores_df


# ─────────────────────────────────────────────────────────────────────────────
# Area aggregation (Appendix A7)
# ─────────────────────────────────────────────────────────────────────────────

def compute_area_scores(factor_scores_df):
    """
    Weighted average of factor indices within each area.
    Also aggregates proficiency and coverage medians separately.
    """
    area_scores = []
    for area in factor_scores_df['area'].unique():
        af = factor_scores_df[factor_scores_df['area'] == area]
        total_weight = af['weight'].sum()
        if total_weight > 0:
            area_index = (af['index_adjusted'] * af['weight']).sum() / total_weight
        else:
            area_index = 1.0

        area_level = int(min(5, max(1, round(area_index))))

        # Aggregate proficiency and coverage
        avg_proficiency = float(af['proficiency_median'].mean()) if 'proficiency_median' in af else area_index
        avg_coverage    = float(af['coverage_median'].mean())    if 'coverage_median'    in af else area_index

        area_scores.append({
            'area':             area,
            'area_index':       area_index,
            'area_level':       area_level,
            'n_factors':        len(af),
            'avg_responses':    float(af['n_responses'].mean()),
            'avg_proficiency':  avg_proficiency,
            'avg_coverage':     avg_coverage,
        })

    return pd.DataFrame(area_scores)


# ─────────────────────────────────────────────────────────────────────────────
# Overall score
# ─────────────────────────────────────────────────────────────────────────────

def compute_overall_score(area_scores_df):
    """Simple (equal-weighted) average of area indices."""
    overall_index = float(area_scores_df['area_index'].mean())
    overall_level = int(min(5, max(1, round(overall_index))))
    overall_proficiency = float(area_scores_df['avg_proficiency'].mean()) if 'avg_proficiency' in area_scores_df else overall_index
    overall_coverage    = float(area_scores_df['avg_coverage'].mean())    if 'avg_coverage'    in area_scores_df else overall_index
    return {
        'overall_index':       overall_index,
        'overall_level':       overall_level,
        'overall_proficiency': overall_proficiency,
        'overall_coverage':    overall_coverage,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Gap analysis and improvement backlog (Appendix B2)
# ─────────────────────────────────────────────────────────────────────────────

def compute_gap_analysis(factor_scores_df, actions_df):
    """
    Match factors below target maturity to applicable Appendix B2 actions.
    Priority = (impact × gap × weight) / effort × quality_factor
    Actions are grouped by level transition (1→2, 2→3, 3→4, 4→5).
    """
    gaps = []
    for _, factor in factor_scores_df.iterrows():
        target_level  = factor['target_level']
        current_level = factor['median_level']
        if pd.isna(current_level):
            current_level = 1.0
        gap_levels = max(0, target_level - current_level)
        if gap_levels <= 0:
            continue

        # Actions applicable when current_level ≤ threshold
        factor_actions = actions_df[
            (actions_df['factor_id'] == factor['factor_id']) &
            (actions_df['if_level_leq'] >= current_level)
        ]

        for _, action in factor_actions.iterrows():
            impact  = action['impact']
            effort  = action['effort']
            # Level transition label (e.g. "Level 2 → 3")
            from_lvl = int(action['if_level_leq'])
            to_lvl   = from_lvl + 1
            transition_label = f"Level {from_lvl} → {to_lvl}"

            priority_score = (impact * gap_levels * factor['weight']) / max(effort, 1)

            # Quality adjustment
            if factor['n_responses'] > 0:
                q_response   = min(1.0, factor['n_responses'] / 5.0)
                q_dispersion = max(0.0, 1.0 - factor['dispersion'] / 2.0) if not pd.isna(factor['dispersion']) else 0.5
                q_evidence   = factor['evidence_rate']
                quality_factor = q_response * q_dispersion * q_evidence
            else:
                quality_factor = 0.1

            priority_score *= quality_factor

            gaps.append({
                'factor_id':          factor['factor_id'],
                'factor_name':        factor['factor_name'],
                'area':               factor['area'],
                'current_level':      current_level,
                'target_level':       target_level,
                'gap_levels':         gap_levels,
                'proficiency_level':  factor.get('proficiency_median', current_level),
                'coverage_level':     factor.get('coverage_median', current_level),
                'action_id':          action['action_id'],
                'action_text':        action['action_text'],
                'transition':         transition_label,
                'impact':             impact,
                'effort':             effort,
                'timeframe':          action['timeframe'],
                'priority_score':     priority_score,
                'owner_group':        factor['owner_group'],
            })

    gaps_df = pd.DataFrame(gaps)
    if len(gaps_df) > 0:
        gaps_df = gaps_df.sort_values('priority_score', ascending=False).reset_index(drop=True)
    return gaps_df


# ─────────────────────────────────────────────────────────────────────────────
# Participation statistics
# ─────────────────────────────────────────────────────────────────────────────

def compute_participation_stats(responses_df, cycle_id):
    """Participation statistics for a given cycle."""
    cycle_data = responses_df[responses_df['cycle_id'] == cycle_id]
    total_respondents = cycle_data['respondent_id'].nunique()
    by_group = cycle_data.groupby('org_group').agg(
        unique_respondents=('respondent_id', 'nunique'),
        total_responses=('factor_id', 'count'),
    )
    return {
        'total_respondents': total_respondents,
        'by_group': by_group,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Trend data across cycles
# ─────────────────────────────────────────────────────────────────────────────

def compute_trend_data(responses_df, factors_df, actions_df):
    """Compute overall, area, and factor scores across all cycles for trend analysis."""
    cycles = responses_df['cycle_id'].unique()
    trend_data = {'overall': [], 'by_area': [], 'by_factor': []}

    for cycle in cycles:
        factor_scores = compute_factor_scores(responses_df, factors_df, cycle)
        area_scores   = compute_area_scores(factor_scores)
        overall       = compute_overall_score(area_scores)

        trend_data['overall'].append({
            'cycle_id':            cycle,
            'overall_index':       overall['overall_index'],
            'overall_level':       overall['overall_level'],
            'overall_proficiency': overall['overall_proficiency'],
            'overall_coverage':    overall['overall_coverage'],
        })

        for _, area in area_scores.iterrows():
            trend_data['by_area'].append({
                'cycle_id':        cycle,
                'area':            area['area'],
                'area_index':      area['area_index'],
                'area_level':      area['area_level'],
                'avg_proficiency': area.get('avg_proficiency', area['area_index']),
                'avg_coverage':    area.get('avg_coverage', area['area_index']),
            })

        for _, factor in factor_scores.head(10).iterrows():
            trend_data['by_factor'].append({
                'cycle_id':      cycle,
                'factor_id':     factor['factor_id'],
                'factor_name':   factor['factor_name'],
                'index_adjusted': factor['index_adjusted'],
            })

    return {
        'overall':   pd.DataFrame(trend_data['overall']),
        'by_area':   pd.DataFrame(trend_data['by_area']),
        'by_factor': pd.DataFrame(trend_data['by_factor']),
    }
