"""
Utility helpers for reservoir-engineering tasks.
"""

def normalize_keyword(kw: str):
    return kw.strip().upper()

def is_positive_number(x):
    try:
        return float(x) > 0
    except:
        return False
