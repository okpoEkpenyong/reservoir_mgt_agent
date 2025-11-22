"""
Simple planning module for converting QC issues into actions.
"""

def build_plan(qc_issues: list, sections: dict):
    """Build an action plan from QC issues and deck sections.

    Args:
        qc_issues (list): List of QC issue strings detected in the deck.
        sections (dict): Mapping of section names to their content strings.

    Returns:
        list: Ordered list of action strings guiding deck corrections.
    """
    plan = []

    if not qc_issues:
        return ["Deck OK. Ready for simulation."]

    for issue in qc_issues:

        if "END" in issue:
            plan.append("Append END keyword at bottom of deck.")

        if "WELSPECS" in issue:
            plan.append("Verify well locations, KD, depth, and coordinates.")

        if "missing" in issue.lower():
            plan.append("Cross-check well naming consistency across sections.")

        if "pressure" in sections.get("SOLUTION", "").lower():
            plan.append("Check SOLUTION initial pressures for realism (>1000 psi).")

    return plan
