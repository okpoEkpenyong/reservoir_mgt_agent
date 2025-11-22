"""QC rules for reservoir management input files.

This module provides simple quality-control checks used by the
reservoir management agent.
"""

import re

def check_end_keyword(content: str):
    """Return True if the 'END' keyword appears anywhere in the content."""
def extract_well_names(block: str):
    """Extract well names quoted with single quotes from a text block and return them as a set."""
    names = set()
    for ln in block.splitlines():
        m = re.search(r"'([^']+)'", ln)
        if m:
            names.add(m.group(1))
    return names

def qc_wellspecs_vs_controls(sections):
    """Compare WELSPECS section against well control sections and return a list of issues.

    Adds an issue when well controls exist but no WELSPECS section is present,
    and when controls reference wells that are missing from WELSPECS.
    """
    issues = []
    wels = sections.get("WELSPECS", "")
    wcon = sections.get("WCONPROD", "") + sections.get("WCONINJE", "")

    if wcon and not wels:
        issues.append("Well controls found but no WELSPECS section.")

    if wels and wcon:
        wels_names = extract_well_names(wels)
        ctrl_names = extract_well_names(wcon)
        missing = ctrl_names - wels_names
        if missing:
            issues.append(f"Wells missing in WELSPECS: {missing}")

    return issues

def run_qc(content: str, sections: dict):
    """Run all QC checks on the provided content and parsed sections, returning a list of issues."""
    issues = []
    if not check_end_keyword(content):
        issues.append("Missing END keyword.")

    issues += qc_wellspecs_vs_controls(sections)

    return issues
