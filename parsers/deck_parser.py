import re
from pathlib import Path
from typing import Dict, List

class DeckParser:
    """
    Lightweight parser for ECLIPSE .DATA decks.
    Extracts keyword-blocks and exposes them as dictionary sections.
    """

    DEFAULT_SECTIONS = [
        "RUNSPEC", "GRID", "EDIT", "PROPS", "REGIONS",
        "SOLUTION", "SUMMARY", "SCHEDULE", "WELSPECS",
        "WCONPROD", "WCONINJE", "COMPDAT", "END"
    ]

    def __init__(self, filepath: str):
        self.path = Path(filepath)
        self.content = self.path.read_text(errors="ignore")
        self.sections: Dict[str, str] = {}

    def extract_sections(self, keywords: List[str] = None):
        if keywords is None:
            keywords = self.DEFAULT_SECTIONS

        lines = self.content.splitlines()
        current_kw = None
        buffer = []

        for line in lines:
            m = re.match(r"^\s*([A-Z0-9_]+)\b", line)
            if m and m.group(1) in keywords:
                if current_kw:
                    self.sections[current_kw] = "\n".join(buffer)
                current_kw = m.group(1)
                buffer = [line]
            else:
                if current_kw:
                    buffer.append(line)

        # last block
        if current_kw:
            self.sections[current_kw] = "\n".join(buffer)

        return self.sections

    def summary(self):
        """Returns counts of lines per section."""
        return {
            k: len(v.splitlines())
            for k, v in self.sections.items()
        }
