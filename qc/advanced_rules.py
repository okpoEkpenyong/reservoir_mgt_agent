def qc_initial_pressure(sections):
    sol = sections.get("SOLUTION", "")
    issues = []
    for line in sol.splitlines():
        if "PRESSURE" in line.upper():
            continue
        try:
            p = float(line.split()[0])
            if p < 500:  # too low for most fields
                issues.append(f"Unrealistic initial pressure: {p} psi.")
        except:
            pass
    return issues


def qc_pvt_completeness(sections):
    props = sections.get("PROPS", "")
    missing = []
    for kw in ["PVTO", "PVTW", "PVTG"]:
        if kw not in props:
            missing.append(kw)
    if missing:
        return [f"Missing PVT tables: {missing}"]
    return []


def qc_compdat(sections):
    comp = sections.get("COMPDAT", "")
    issues = []
    for ln in comp.splitlines():
        if "OPEN" not in ln.upper():
            issues.append("COMPDAT entry missing OPEN/CLOSED keyword.")
    return issues
