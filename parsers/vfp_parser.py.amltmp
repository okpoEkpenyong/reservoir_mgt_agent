import re
from typing import Dict, List

class VFPParser:
    """
    Minimal parser for .VFP tables.
    Extracts:
    - VFP table numbers
    - Flow conditions
    - Rate tables
    """

    def parse(self, text: str) -> Dict:
        tables = {}
        current_table = None
        buffer: List[str] = []

        for ln in text.splitlines():
            header = re.match(r'\s*VFP(\d+)', ln)
            if header:
                if current_table:
                    tables[current_table] = "\n".join(buffer)
                current_table = header.group(1)
                buffer = []
            else:
                if current_table:
                    buffer.append(ln)

        if current_table:
            tables[current_table] = "\n".join(buffer)

        return tables
