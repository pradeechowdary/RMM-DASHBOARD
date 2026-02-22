"""
Generate realistic dummy data for RMM Dashboard prototype
Aligned with Appendix B: RMM Instrument questionnaire components and
Appendix A: dual Proficiency / Coverage scoring model
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_factors():
    """
    Factor catalog aligned with Appendix B questionnaire.
    Block 1 = Project Management        (Q7-Q21)
    Block 2 = Evaluation & Impact Measurement (Q22-Q35)
    Block 3 = Invoicing Process         (Q36-Q48)
    Area names match Appendix A1 domain labels exactly.
    """
    factors_data = []

    pm_factors = [
        ("PM_01", "Project Solicitation & Prioritization",
         "How research needs are converted into candidate projects and prioritized (Q7-Q8)"),
        ("PM_02", "Scope Definition & Change Control",
         "How scope is defined to stabilise expectations and how changes are controlled (Q9, Q15)"),
        ("PM_03", "Roles & Responsibilities",
         "How roles and responsibilities are established and enforced across project teams (Q10)"),
        ("PM_04", "Schedule & Milestone Planning",
         "How schedules and milestones are planned and updated during execution (Q11)"),
        ("PM_05", "Progress Reporting",
         "How progress reporting is structured during project execution (Q12)"),
        ("PM_06", "Technical Review & Approval",
         "How technical reviews and approvals are handled for deliverables (Q13)"),
        ("PM_07", "Issue & Risk Management",
         "How delays, missing data, contractor capacity issues, and scope drift are handled (Q14)"),
        ("PM_08", "Records Management & Archival",
         "How project records are organised for future retrieval (Q16)"),
        ("PM_09", "Vendor & Contractor Performance",
         "How vendor/contractor performance is managed and quality expectations enforced (Q17-Q18)"),
        ("PM_10", "Project Closure & Lessons Learned",
         "How project closure is conducted and lessons learned are captured and reused (Q19-Q20)"),
        ("PM_11", "Organisational Consistency",
         "How consistent project management practices are across organisational groups (Q21)"),
    ]

    eim_factors = [
        ("EIM_01", "Outcome Definition",
         "How expected results are defined before project work begins (Q22)"),
        ("EIM_02", "Research Usefulness Evaluation",
         "How the usefulness of research is judged after project completion (Q23)"),
        ("EIM_03", "Technology Transfer & Usability",
         "How research results are translated into outputs operational staff can use (Q24)"),
        ("EIM_04", "Implementation Tracking",
         "How implementation of research outcomes is tracked post-closure (Q25)"),
        ("EIM_05", "Barrier Analysis",
         "How causes of non-implementation or non-adoption are identified and addressed (Q26)"),
        ("EIM_06", "Reporting Quality & Standards",
         "How consistent project reporting quality is across projects (Q27)"),
        ("EIM_07", "Internal Communication of Findings",
         "How evaluation findings are communicated internally after project completion (Q28)"),
        ("EIM_08", "Stakeholder Involvement in Evaluation",
         "How stakeholders are involved in judging project outcomes (Q29)"),
        ("EIM_09", "Post-Delivery Feedback Collection",
         "How feedback is collected after deliverables are used or tested in real settings (Q30)"),
        ("EIM_10", "Strategic Alignment",
         "How evaluation results connect to agency priorities or strategic objectives (Q31)"),
        ("EIM_11", "Evaluation Records Management",
         "How evaluation records are organised for retrieval and reuse (Q32)"),
        ("EIM_12", "Long-Term Impact Assessment",
         "How long-term impact of research projects is assessed (Q33)"),
        ("EIM_13", "Evaluation Consistency & Improvement",
         "How consistent evaluation practices are and how they improve over time (Q34-Q35)"),
    ]

    inv_factors = [
        ("INV_01", "Invoice Submission Requirements",
         "How invoice submission requirements are communicated to contractors (Q36)"),
        ("INV_02", "Invoice Package Consistency",
         "How consistent invoice packages are when received for review (Q37)"),
        ("INV_03", "Invoice Review Process",
         "How invoices are reviewed after submission with defined checks (Q38)"),
        ("INV_04", "Approval Responsibilities",
         "How approval responsibilities are defined and managed during processing (Q39)"),
        ("INV_05", "Processing Timeliness",
         "How predictable invoice processing time is from submission to final approval (Q40)"),
        ("INV_06", "Error Correction & Issue Handling",
         "How incomplete or incorrect invoices are managed once problems are identified (Q41)"),
        ("INV_07", "Communication During Review",
         "How communication is maintained with submitters during invoice review (Q42)"),
        ("INV_08", "Invoicing Records Management",
         "How invoicing records are organised for audits or issue resolution (Q43)"),
        ("INV_09", "Recurring Issue Identification",
         "How recurring invoicing issues are identified and addressed across projects (Q44)"),
        ("INV_10", "Administrative-Technical Coordination",
         "How coordination is managed between administrative and technical reviewers (Q45)"),
        ("INV_11", "Requirements Communication & Consistency",
         "How changes to invoicing requirements are communicated across groups (Q46-Q47)"),
        ("INV_12", "Invoicing Process Improvement",
         "How the invoicing process improves over time using performance data (Q48)"),
    ]

    all_areas = [
        ("Project Management", pm_factors),
        ("Evaluation & Impact Measurement", eim_factors),
        ("Invoicing Process", inv_factors),
    ]

    for area, factors in all_areas:
        for factor_id, name, desc in factors:
            factors_data.append({
                'factor_id': factor_id,
                'area': area,
                'factor_name': name,
                'description': desc,
                'weight': np.random.choice([1.0, 1.2, 0.8], p=[0.7, 0.15, 0.15]),
                'target_level': np.random.choice([3, 4], p=[0.6, 0.4]),
                'owner_group': np.random.choice(
                    ['Program Office', 'Technical Leads', 'Finance', 'Admin'],
                    p=[0.4, 0.3, 0.2, 0.1]),
                'evidence_required': np.random.choice([0, 1], p=[0.3, 0.7]),
            })

    return pd.DataFrame(factors_data)


def generate_responses(factors_df, num_cycles=3):
    """
    Assessment responses with dual Proficiency + Coverage dimensions per Appendix A2-A5.
    proficiency_level = how well the practice is performed (1-5)
    coverage_level    = how widely the practice is adopted across groups (1-5)
    level             = combined maturity = min(proficiency, coverage) per Appendix A5:
                        true maturity requires BOTH high proficiency AND broad coverage
    """
    org_groups = ['Program Office', 'Admin', 'Technical Leads', 'Finance', 'Field Teams']
    responses_data = []
    base_date = datetime(2024, 1, 15)

    for cycle in range(num_cycles):
        cycle_id = f"cycle_{cycle}" if cycle > 0 else "baseline"
        cycle_date = base_date + timedelta(days=180 * cycle)

        for _, factor in factors_df.iterrows():
            factor_id = factor['factor_id']
            base_prof = np.random.choice([1, 2, 3, 4, 5], p=[0.05, 0.25, 0.40, 0.25, 0.05])
            base_cov  = np.random.choice([1, 2, 3, 4, 5], p=[0.08, 0.30, 0.35, 0.20, 0.07])
            # Slight improvement each cycle
            base_prof = min(5, base_prof + cycle * 0.3)
            base_cov  = min(5, base_cov  + cycle * 0.2)

            num_respondents = np.random.randint(3, 8)
            for resp_idx in range(num_respondents):
                org_group    = np.random.choice(org_groups)
                proficiency  = int(np.clip(base_prof + np.random.normal(0, 0.6), 1, 5))
                coverage     = int(np.clip(base_cov  + np.random.normal(0, 0.7), 1, 5))
                combined     = min(proficiency, coverage)   # Appendix A5 combined logic

                confidence   = np.random.choice([3, 4, 5], p=[0.2, 0.5, 0.3])
                has_evidence = np.random.random() < 0.4
                evidence_link = f"doc_{factor_id}_{resp_idx}.pdf" if has_evidence else None
                has_notes     = np.random.random() < 0.3
                free_text     = f"Notes on {factor['factor_name']}" if has_notes else None

                responses_data.append({
                    'cycle_id':          cycle_id,
                    'respondent_id':     f"resp_{resp_idx}_{org_group[:3]}",
                    'org_group':         org_group,
                    'factor_id':         factor_id,
                    'level':             combined,       # backward-compat combined score
                    'proficiency_level': proficiency,
                    'coverage_level':    coverage,
                    'confidence':        confidence,
                    'free_text':         free_text,
                    'evidence_link':     evidence_link,
                    'timestamp':         cycle_date + timedelta(days=np.random.randint(0, 30)),
                })

    return pd.DataFrame(responses_data)


def generate_actions(factors_df):
    """
    Improvement actions aligned with Appendix B2 action guidance tables.
    Level 1→2: informal → basic repeatable
    Level 2→3: formalise and standardise across groups
    Level 3→4: introduce performance metrics
    Level 4→5: institutionalise continuous improvement
    """
    action_templates = {
        1: [
            ("Develop standardised {factor} templates covering scope, roles, milestones, and reporting expectations", 4, 2, "short"),
            ("Introduce basic {factor} reporting cadence with minimum standard reporting structure", 3, 1, "short"),
        ],
        2: [
            ("Formalise {factor} review and approval procedures with defined roles and workflows", 4, 3, "medium"),
            ("Implement structured {factor} issue tracking with consistent escalation rules", 3, 2, "medium"),
            ("Deploy {factor} templates agency-wide and train staff to drive organisational consistency", 3, 2, "short"),
        ],
        3: [
            ("Introduce measurable {factor} performance indicators (schedule adherence, turnaround, acceptance rate)", 5, 3, "medium"),
            ("Standardise {factor} review management with checklists, time-tracking, and escalation paths", 4, 3, "medium"),
            ("Formalise lessons-learned integration for {factor} through structured closeout reviews", 3, 2, "short"),
        ],
        4: [
            ("Use historical {factor} data for proactive planning refinement and scheduling improvement", 5, 4, "long"),
            ("Institutionalise cross-project {factor} knowledge reuse in an organised, searchable repository", 5, 5, "long"),
            ("Establish continuous {factor} improvement governance cycle with quarterly or semi-annual reviews", 4, 3, "medium"),
        ],
    }

    actions_data = []
    action_id = 1
    for _, factor in factors_df.iterrows():
        factor_id   = factor['factor_id']
        factor_name = factor['factor_name']
        for threshold, templates in action_templates.items():
            for template, impact, effort, timeframe in templates:
                actions_data.append({
                    'action_id':             f"ACT_{action_id:03d}",
                    'factor_id':             factor_id,
                    'if_level_leq':          threshold,
                    'action_text':           template.format(factor=factor_name),
                    'impact':                impact,
                    'effort':                effort,
                    'timeframe':             timeframe,
                    'dependency_action_id':  None,
                })
                action_id += 1

    return pd.DataFrame(actions_data)


def generate_all_data(output_dir='data'):
    """Generate all dummy data files."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    print("Generating dummy data aligned with Appendix B questionnaire…")

    factors_df = generate_factors()
    factors_df.to_csv(f'{output_dir}/factors.csv', index=False)
    pm  = (factors_df.area == 'Project Management').sum()
    eim = (factors_df.area == 'Evaluation & Impact Measurement').sum()
    inv = (factors_df.area == 'Invoicing Process').sum()
    print(f"  ✔ {len(factors_df)} factors — PM: {pm}, EIM: {eim}, INV: {inv}")

    responses_df = generate_responses(factors_df, num_cycles=3)
    responses_df.to_csv(f'{output_dir}/responses.csv', index=False)
    print(f"  ✔ {len(responses_df)} responses across 3 cycles (includes proficiency_level + coverage_level)")

    actions_df = generate_actions(factors_df)
    actions_df.to_csv(f'{output_dir}/actions.csv', index=False)
    print(f"  ✔ {len(actions_df)} improvement actions (Level 1→2 through 4→5)")

    print("\nData generation complete!")
    return factors_df, responses_df, actions_df


if __name__ == "__main__":
    generate_all_data()
