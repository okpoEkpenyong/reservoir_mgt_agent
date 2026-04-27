"""
reservoir_keywords.py
─────────────────────────────────────────────────────────────────────────────
Unified ECLIPSE / OPM Flow keyword query interface.

Usage
-----
    from keyword_query import KeywordDB

    db = KeywordDB("reservoir_keywords_db_v3.json")

    # Look up a keyword
    kw = db.get("WELSPECS")

    # Search
    results = db.search("well production control")

    # Filter by section
    schedule_kws = db.by_section("SCHEDULE")

    # OPM support check
    supported = db.opm_supported_keywords()
    not_supported = db.opm_unsupported_keywords()

    # For your agent: ground-truth answer
    answer = db.agent_answer("COMPDAT")
"""

import json
import re
from pathlib import Path
from typing import Optional


class KeywordDB:
    """Queryable ECLIPSE/OPM keyword ground-truth database."""

    def __init__(self, db_path: str = "reservoir_keywords_db_v3.json"):
        path = Path(db_path)
        if not path.exists():
            raise FileNotFoundError(f"DB not found: {db_path}")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self._meta     = data["_metadata"]
        self._indexes  = data["indexes"]
        self._keywords = data["keywords"]
        print(f"[KeywordDB] Loaded {len(self._keywords):,} keywords  |  "
              f"Sources: ECLIPSE 2022.2 + OPM 2025-10 + ECLIPSE Tech Desc")

    # ── Core lookup ─────────────────────────────────────────────────────────

    def get(self, keyword: str) -> Optional[dict]:
        """Return the full record for a keyword (case-insensitive)."""
        return self._keywords.get(keyword.upper())

    def exists(self, keyword: str) -> bool:
        return keyword.upper() in self._keywords

    # ── Search ───────────────────────────────────────────────────────────────

    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Full-text search across keyword name, title, description, and OPM description.
        Returns list of (score, record) sorted by relevance.
        """
        q_tokens = re.findall(r'\w+', query.lower())
        results = []

        for kw, rec in self._keywords.items():
            text = ' '.join([
                kw.lower(),
                rec.get("title", "").lower(),
                rec.get("description", "").lower(),
                rec.get("opm_description", "").lower(),
            ])
            score = sum(text.count(t) for t in q_tokens)
            # Bonus for keyword name match
            if any(t in kw.lower() for t in q_tokens):
                score += 5
            if score > 0:
                results.append((score, rec))

        results.sort(key=lambda x: -x[0])
        return [r for _, r in results[:max_results]]

    # ── Filter by section ────────────────────────────────────────────────────

    def by_section(self, section: str) -> list[str]:
        """Return sorted list of keyword names valid in a given section."""
        section = section.upper()
        idx = self._indexes.get("by_section", {})
        return idx.get(section, [])

    # ── OPM support filters ──────────────────────────────────────────────────

    def opm_supported_keywords(self) -> list[str]:
        return self._indexes["by_opm_support"]["supported"]

    def opm_unsupported_keywords(self) -> list[str]:
        return self._indexes["by_opm_support"]["not_supported"]

    def opm_ignored_keywords(self) -> list[str]:
        return self._indexes["by_opm_support"]["ignored"]

    def check_opm_support(self, keyword: str) -> dict:
        """Return OPM support status for a keyword."""
        rec = self.get(keyword)
        if not rec:
            return {"keyword": keyword, "found": False}
        sup = rec.get("opm_supported")
        label = {
            True:      "✅ Supported",
            False:     "❌ Not supported",
            "ignored": "⚠️  Ignored (no effect)",
            "partial": "🔶 Partial support",
            None:      "❓ Unknown / ECLIPSE-only"
        }.get(sup, "❓ Unknown")
        return {
            "keyword":    keyword.upper(),
            "found":      True,
            "status":     label,
            "raw":        sup,
            "notes":      rec.get("opm_notes", ""),
            "sources":    rec.get("sources", [])
        }

    # ── Agent-ready ground-truth summary ─────────────────────────────────────

    def agent_answer(self, keyword: str, verbose: bool = False) -> str:
        """
        Return a concise, ground-truth text answer about a keyword.
        Suitable for injecting into a reservoir agent's context.
        """
        rec = self.get(keyword)
        if not rec:
            # Try fuzzy match
            candidates = self.search(keyword, max_results=3)
            if candidates:
                names = [c["keyword"] for c in candidates]
                return f"Keyword '{keyword}' not found. Did you mean: {', '.join(names)}?"
            return f"Keyword '{keyword}' not found in the database."

        kw   = rec["keyword"]
        title = rec.get("title", "")
        secs  = rec.get("sections", [])
        e100  = rec.get("eclipse_100")
        e300  = rec.get("eclipse_300")
        desc  = rec.get("description") or rec.get("opm_description", "")
        opm_sup = rec.get("opm_supported")
        opm_note = rec.get("opm_notes", "")
        params = rec.get("opm_parameters") or rec.get("items", [])
        units  = rec.get("units", {})
        defs   = rec.get("defaults", [])
        example= rec.get("opm_example") or rec.get("example", "")

        opm_labels = {
            True:      "✅ Supported in OPM Flow",
            False:     "❌ NOT supported in OPM Flow",
            "ignored": "⚠️  Accepted but ignored by OPM Flow (no effect on results)",
            "partial": "🔶 Partially supported in OPM Flow",
            None:      "❓ OPM support status unknown"
        }

        lines = [f"## {kw}"]
        if title:
            lines.append(f"**{title}**")
        lines.append("")

        if secs:
            lines.append(f"**Valid in sections:** {', '.join(secs)}")
        
        sim_support = []
        if e100 is True:  sim_support.append("ECLIPSE 100")
        if e300 is True:  sim_support.append("ECLIPSE 300")
        if sim_support:
            lines.append(f"**Simulator support:** {', '.join(sim_support)}")
        
        lines.append(f"**OPM Flow:** {opm_labels.get(opm_sup, '❓ Unknown')}")
        if opm_note:
            lines.append(f"  → {opm_note}")
        lines.append("")

        if desc:
            lines.append(f"**Description:**")
            lines.append(desc[:600])
            lines.append("")

        if params and verbose:
            lines.append("**Parameters:**")
            for p in params[:10]:
                no   = p.get("no") or p.get("item", "?")
                name = p.get("name", "")
                pdesc= p.get("description") or p.get("text", "")
                dfl  = p.get("default", "")
                if name:
                    lines.append(f"  {no}. `{name}` – {pdesc[:120]}"
                                 + (f" *(default: {dfl})*" if dfl else ""))
                else:
                    lines.append(f"  {no}. {pdesc[:140]}")
            lines.append("")

        if units:
            u_str = ", ".join(f"{v} ({k})" for k, v in list(units.items())[:4])
            lines.append(f"**Units:** {u_str}")

        if defs:
            lines.append(f"**Defaults:** {' | '.join(defs[:3])}")

        if example:
            lines.append(f"\n**Example:**\n```\n{example[:400]}\n```")

        sources = rec.get("sources", [])
        lines.append(f"\n*Sources: {', '.join(sources)}*")

        return '\n'.join(lines)

    # ── Bulk export helpers ──────────────────────────────────────────────────

    def export_section_list(self, section: str) -> str:
        """Return a formatted list of all keywords in a section."""
        kws = self.by_section(section)
        lines = [f"# Keywords valid in {section.upper()} section ({len(kws)} total)\n"]
        for kw in kws:
            rec = self._keywords[kw]
            title = rec.get("title", "")
            opm = rec.get("opm_supported")
            opm_icon = {True:"✅",False:"❌","ignored":"⚠️","partial":"🔶",None:"❓"}.get(opm,"❓")
            lines.append(f"  {opm_icon} {kw:<20} {title[:60]}")
        return '\n'.join(lines)

    def export_opm_compatibility_report(self) -> str:
        """Generate an OPM compatibility report for all keywords."""
        idx = self._indexes["by_opm_support"]
        lines = [
            "# OPM Flow Compatibility Report",
            f"Source: OPM Flow Reference Manual 2025-10",
            "",
            f"## ✅ Fully Supported ({len(idx['supported'])} keywords)",
            ', '.join(idx['supported']),
            "",
            f"## ❌ Not Supported ({len(idx['not_supported'])} keywords)",
            ', '.join(idx['not_supported']),
            "",
            f"## ⚠️  Ignored / No Effect ({len(idx['ignored'])} keywords)",
            ', '.join(idx['ignored']),
            "",
            f"## 🔶 Partial Support ({len(idx['partial'])} keywords)",
            ', '.join(idx['partial']),
            "",
            f"## ❓ Unknown / ECLIPSE-only ({len(idx['unknown'])} keywords)",
            ', '.join(idx['unknown'][:50]) + (" ..." if len(idx['unknown']) > 50 else ""),
        ]
        return '\n'.join(lines)

    def stats(self) -> dict:
        return self._meta["stats"]

    def __len__(self):
        return len(self._keywords)

    def __contains__(self, keyword: str):
        return self.exists(keyword)

    def __repr__(self):
        s = self._meta["stats"]
        return (f"<KeywordDB {s['total_keywords']} keywords | "
                f"ECLIPSE 2022.2 + OPM 2025-10>")


# ── Quick demo / self-test ──────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] 
    db = KeywordDB(db_path)
    print(repr(db))
    print()

    # Test key lookups
    for kw in ["WELSPECS","COMPDAT","WCONPROD","PVTO","SWOF","PERMX","ACTIONX","WSEGVALV"]:
        sup = db.check_opm_support(kw)
        rec = db.get(kw)
        secs = rec.get("sections", []) if rec else []
        print(f"  {sup['status']:<35} | {kw:<14} | secs={secs}")

    print()
    print("─── WELSPECS agent_answer ───")
    print(db.agent_answer("WELSPECS", verbose=True))

    print()
    print("─── Search: 'well injection control' ───")
    results = db.search("well injection control", max_results=5)
    for r in results:
        print(f"  {r['keyword']:<14}  {r.get('title','')[:60]}")

    print()
    print("─── SCHEDULE section (first 20) ───")
    schedule_kws = db.by_section("SCHEDULE")
    print(f"  Total: {len(schedule_kws)}")
    print("  ", schedule_kws[:20])
