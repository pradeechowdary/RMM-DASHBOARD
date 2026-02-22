"""
Data Validation Script – RMM Dashboard
Aligned with Appendix A1 domain names and Appendix B questionnaire structure
"""
import pandas as pd
import sys

# Appendix A1 domain labels (must match factors.csv area column exactly)
VALID_AREAS = [
    "Project Management",
    "Evaluation & Impact Measurement",
    "Invoicing Process",
]


def validate_factors(factors_df):
    errors, warnings = [], []

    required_cols = ['factor_id', 'area', 'factor_name', 'weight', 'target_level',
                     'owner_group', 'evidence_required']
    missing = [c for c in required_cols if c not in factors_df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")

    if 'factor_id' in factors_df.columns and factors_df['factor_id'].duplicated().any():
        errors.append("Duplicate factor_ids found")

    if 'area' in factors_df.columns:
        invalid = factors_df[~factors_df['area'].isin(VALID_AREAS)]['area'].unique()
        if len(invalid) > 0:
            errors.append(
                f"Invalid area names: {invalid.tolist()}\n"
                f"  Valid areas (Appendix A1): {VALID_AREAS}"
            )

    if 'target_level' in factors_df.columns:
        if (factors_df['target_level'] < 1).any() or (factors_df['target_level'] > 5).any():
            errors.append("Target levels must be 1–5 (Appendix A6 maturity stages)")

    if 'weight' in factors_df.columns and (factors_df['weight'] == 1.0).all():
        warnings.append("All factors have equal weight (1.0) – consider adjusting for priority components")

    return errors, warnings


def validate_responses(responses_df, factors_df):
    errors, warnings = [], []

    required_cols = ['cycle_id', 'respondent_id', 'org_group', 'factor_id', 'level', 'timestamp']
    missing = [c for c in required_cols if c not in responses_df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")

    # Warn (not error) if dual-dimension columns are absent
    if 'proficiency_level' not in responses_df.columns:
        warnings.append(
            "Column 'proficiency_level' not found – dual Proficiency/Coverage analysis "
            "(Appendix A2-A5) will be unavailable. Regenerate data to include this column."
        )
    if 'coverage_level' not in responses_df.columns:
        warnings.append(
            "Column 'coverage_level' not found – dual Proficiency/Coverage analysis "
            "(Appendix A2-A5) will be unavailable. Regenerate data to include this column."
        )

    if 'factor_id' in responses_df.columns and factors_df is not None:
        valid_factors  = set(factors_df['factor_id'])
        invalid_factors = set(responses_df['factor_id']) - valid_factors
        if invalid_factors:
            errors.append(f"Responses reference unknown factor_ids: {invalid_factors}")

    if 'level' in responses_df.columns:
        invalid_levels = responses_df[~responses_df['level'].between(1, 5)]
        if len(invalid_levels) > 0:
            errors.append(f"{len(invalid_levels)} responses have level values outside 1–5")

    if 'proficiency_level' in responses_df.columns:
        inv = responses_df[~responses_df['proficiency_level'].between(1, 5)]
        if len(inv) > 0:
            errors.append(f"{len(inv)} responses have proficiency_level outside 1–5")

    if 'coverage_level' in responses_df.columns:
        inv = responses_df[~responses_df['coverage_level'].between(1, 5)]
        if len(inv) > 0:
            errors.append(f"{len(inv)} responses have coverage_level outside 1–5")

    if factors_df is not None:
        for factor_id in factors_df['factor_id']:
            fr = responses_df[responses_df['factor_id'] == factor_id] if 'factor_id' in responses_df.columns else pd.DataFrame()
            if len(fr) == 0:
                warnings.append(f"No responses for factor: {factor_id}")
            elif len(fr) < 3:
                warnings.append(f"Low response count ({len(fr)}) for factor: {factor_id}")

    return errors, warnings


def validate_actions(actions_df, factors_df):
    errors, warnings = [], []

    required_cols = ['action_id', 'factor_id', 'if_level_leq', 'action_text',
                     'impact', 'effort', 'timeframe']
    missing = [c for c in required_cols if c not in actions_df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")

    if factors_df is not None and 'factor_id' in actions_df.columns:
        valid_factors   = set(factors_df['factor_id'])
        invalid_factors = set(actions_df['factor_id']) - valid_factors
        if invalid_factors:
            errors.append(f"Actions reference unknown factor_ids: {invalid_factors}")

    if 'timeframe' in actions_df.columns:
        invalid_tf = actions_df[~actions_df['timeframe'].isin(['short', 'medium', 'long'])]
        if len(invalid_tf) > 0:
            errors.append("Invalid timeframes found (must be short / medium / long)")

    if 'impact' in actions_df.columns:
        if (actions_df['impact'] < 1).any() or (actions_df['impact'] > 5).any():
            errors.append("Impact scores must be 1–5")

    if 'effort' in actions_df.columns:
        if (actions_df['effort'] < 1).any() or (actions_df['effort'] > 5).any():
            errors.append("Effort scores must be 1–5")

    if 'if_level_leq' in actions_df.columns:
        invalid_thresh = actions_df[~actions_df['if_level_leq'].between(1, 4)]
        if len(invalid_thresh) > 0:
            warnings.append(
                "Action thresholds (if_level_leq) outside 1–4 found. "
                "Appendix B2 defines transitions for Level 1→2, 2→3, 3→4, and 4→5."
            )

    if factors_df is not None and 'factor_id' in actions_df.columns:
        no_actions = set(factors_df['factor_id']) - set(actions_df['factor_id'])
        if no_actions:
            warnings.append(f"{len(no_actions)} factors have no improvement actions defined")

    return errors, warnings


def main():
    print("=" * 65)
    print("  RMM Dashboard – Data Validation")
    print("  Aligned with Appendix A (framework) & Appendix B (questionnaire)")
    print("=" * 65)

    try:
        print("\nLoading data files…")
        factors_df   = pd.read_csv('data/factors.csv')
        responses_df = pd.read_csv('data/responses.csv')
        actions_df   = pd.read_csv('data/actions.csv')
        print("  ✔ All files loaded")

        all_errors, all_warnings = [], []

        print("\nValidating factors.csv (Appendix A1 domain labels)…")
        e, w = validate_factors(factors_df)
        all_errors   += [f"[factors.csv]   {x}" for x in e]
        all_warnings += [f"[factors.csv]   {x}" for x in w]
        print(f"  {len(factors_df)} factors | {len(e)} errors | {len(w)} warnings")

        print("\nValidating responses.csv (Appendix A2-A5 dual dimensions)…")
        e, w = validate_responses(responses_df, factors_df)
        all_errors   += [f"[responses.csv] {x}" for x in e]
        all_warnings += [f"[responses.csv] {x}" for x in w]
        has_dual = ('proficiency_level' in responses_df.columns and
                    'coverage_level'    in responses_df.columns)
        print(f"  {len(responses_df)} responses | {responses_df['cycle_id'].nunique()} cycles | "
              f"{responses_df['respondent_id'].nunique()} respondents")
        print(f"  Dual dimensions (Appendix A2-A5): {'✔ present' if has_dual else '⚠ absent'}")
        print(f"  {len(e)} errors | {len(w)} warnings")

        print("\nValidating actions.csv (Appendix B2 action guidance)…")
        e, w = validate_actions(actions_df, factors_df)
        all_errors   += [f"[actions.csv]   {x}" for x in e]
        all_warnings += [f"[actions.csv]   {x}" for x in w]
        print(f"  {len(actions_df)} actions | {len(e)} errors | {len(w)} warnings")

        print("\n" + "=" * 65)
        print("VALIDATION SUMMARY")
        print("=" * 65)

        if all_errors:
            print(f"\n❌ {len(all_errors)} ERROR(S):")
            for err in all_errors:
                print(f"  - {err}")
            print("\n⚠️  Fix errors before launching the dashboard.")
            sys.exit(1)
        else:
            print("\n✅ No critical errors found!")

        if all_warnings:
            print(f"\n⚠️  {len(all_warnings)} WARNING(S):")
            for w in all_warnings:
                print(f"  - {w}")
        else:
            print("✅ No warnings!")

        print("\n" + "=" * 65)
        print("Data validation complete. Dashboard is ready to run!")
        print("=" * 65)

    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("Run: python src/generate_dummy_data.py  to create sample data")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
