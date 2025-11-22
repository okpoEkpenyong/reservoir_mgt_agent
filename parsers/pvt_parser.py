import re
from typing import Dict

class PVTParser:
    """
    Extracts PVT tables (PVTO, PVTW, PVTG).
    Basic structural extraction, no interpolation yet.
    """

    KEYWORDS = ["PVTO", "PVTG", "PVTW"]

    def parse(self, text: str) -> Dict[str, str]:
        blocks = {}
        current_kw = None
        buffer = []

        for ln in text.splitlines():
            m = re.match(r"^\s*([A-Z0-9]+)\b", ln)
            if m and m.group(1) in self.KEYWORDS:
                if current_kw:
                    blocks[current_kw] = "\n".join(buffer)
                current_kw = m.group(1)
                buffer = []
            else:
                if current_kw:
                    buffer.append(ln)

        if current_kw:
            blocks[current_kw] = "\n".join(buffer)

        return blocks
