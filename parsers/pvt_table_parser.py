from __future__ import annotations
import re
import io
import json
from typing import Optional, Dict, Any, List, Union, Callable
import numpy as np
import pandas as pd

"""
pvt_parser.py

Parser utilities for reservoir PVT (Pressure-Volume-Temperature) tables.

Provides a PVTParser class that can read PVT data from:
- CSV strings or files
- Excel files (first sheet)
- JSON strings or files
- Plain text tables with whitespace-separated columns

Returns normalized pandas.DataFrame and offers simple interpolation
of PVT properties at arbitrary pressures.

Dependencies: pandas, numpy
"""



# Common column name mapping to normalized keys
_COLUMN_MAP = {
    r'pressure|press|p': 'pressure',
    r'rs|solution\s*gas\s*oil\s*ratio': 'rs',
    r'bo|bv|formation\s*volume\s*factor|b[o0]': 'bo',
    r'visc|mu|viscosity': 'viscosity',
    r'bg|gas\s*fvf|gas\s*formation\s*volume\s*factor': 'bg',
    r'pb|bubble\s*point': 'bubble_point',
    r't|temp|temperature': 'temperature',
    r'so|swi|sw': 'saturation_water',
}


def _normalize_colname(name: str) -> str:
    n = name.strip().lower()
    for pattern, target in _COLUMN_MAP.items():
        if re.search(r'\b' + pattern + r'\b', n):
            return target
    # fallback: remove non-alnum and return
    return re.sub(r'[^a-z0-9_]+', '_', n)


class PVTParser:
    """
    Parse PVT tables and provide interpolation utilities.

    Usage:
      parser = PVTParser.from_csv(csv_text)
      df = parser.df
      props = parser.get_properties(pressure=1500)  # interpolated

    The class keeps a DataFrame with a 'pressure' column (float) in ascending order.
    """

    def __init__(self, df: pd.DataFrame):
        if 'pressure' not in df.columns:
            raise ValueError("DataFrame must contain a 'pressure' column")
        # normalize column names
        df = df.rename(columns={c: _normalize_colname(c) for c in df.columns})
        # ensure numeric
        df = df.apply(pd.to_numeric, errors='coerce')
        # drop rows without pressure
        df = df.dropna(subset=['pressure'])
        # sort ascending by pressure
        df = df.sort_values('pressure').reset_index(drop=True)
        self.df = df

    @classmethod
    def from_csv(cls, csv_input: Union[str, io.StringIO], sep: Optional[str] = None, **kwargs) -> "PVTParser":
        """
        Create parser from CSV string or file path. If sep is None, pandas will try to infer.
        """
        if isinstance(csv_input, str) and '\n' in csv_input:
            data = io.StringIO(csv_input)
        else:
            data = csv_input
        df = pd.read_csv(data, sep=sep, **kwargs)
        return cls(df)

    @classmethod
    def from_excel(cls, path_or_buffer: Union[str, io.BytesIO], sheet_name=0, **kwargs) -> "PVTParser":
        df = pd.read_excel(path_or_buffer, sheet_name=sheet_name, **kwargs)
        return cls(df)

    @classmethod
    def from_json(cls, json_input: Union[str, Dict, List]) -> "PVTParser":
        """
        Accepts a JSON string or python object representing a list of records or a dict of lists.
        """
        if isinstance(json_input, str):
            parsed = json.loads(json_input)
        else:
            parsed = json_input
        df = pd.DataFrame(parsed)
        return cls(df)

    @classmethod
    def from_text_table(cls, text: str, delimiter: Optional[str] = None) -> "PVTParser":
        """
        Parse a plain text table where the first non-empty line is a header.
        Supports fixed-width, whitespace-separated or delimiter-separated tables.
        """
        lines = [ln for ln in text.splitlines() if ln.strip()]
        if not lines:
            raise ValueError("Empty text")
        header_line = lines[0]
        # Try to detect delimiter by common separators
        if delimiter is None:
            for d in [',', '\t', ';', '|']:
                if d in header_line:
                    delimiter = d
                    break
        if delimiter:
            buf = io.StringIO("\n".join(lines))
            df = pd.read_csv(buf, sep=delimiter)
            return cls(df)
        else:
            # whitespace separated; use pandas.read_csv with delim_whitespace
            buf = io.StringIO("\n".join(lines))
            df = pd.read_csv(buf, delim_whitespace=True)
            return cls(df)

    def to_json(self, orient='records', **kwargs) -> str:
        return self.df.to_json(orient=orient, **kwargs)

    def to_csv(self, **kwargs) -> str:
        return self.df.to_csv(index=False, **kwargs)

    def validate(self) -> Dict[str, Any]:
        """
        Basic validation: checks monotonic pressure and missing critical columns.
        Returns a report dict.
        """
        report: Dict[str, Any] = {}
        if self.df['pressure'].is_monotonic_increasing:
            report['pressure_monotonic'] = True
        else:
            report['pressure_monotonic'] = False
            report['pressure_duplicates'] = int(self.df['pressure'].duplicated().sum())
        # required columns? allow bo or rs or viscosity optional
        report['columns'] = list(self.df.columns)
        report['nan_counts'] = self.df.isna().sum().to_dict()
        return report

    def _interp_column(self, col: str, method: str = 'linear') -> Callable[[float], Optional[float]]:
        """
        Return a function that interpolates column 'col' over pressure.
        If column not present or all NaN, returns function that always returns None.
        """
        if col not in self.df.columns or self.df[col].dropna().empty:
            return lambda p: None
        pressures = self.df['pressure'].values
        vals = self.df[col].values
        # handle NaNs by masking
        mask = ~np.isnan(vals)
        if mask.sum() == 0:
            return lambda p: None
        p_use = pressures[mask]
        v_use = vals[mask]
        def interp(p: float) -> float:
            # extrapolate using nearest
            if p <= p_use[0]:
                return float(v_use[0])
            if p >= p_use[-1]:
                return float(v_use[-1])
            return float(np.interp(p, p_use, v_use))
        return interp

    def get_properties(self, pressure: float, properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get interpolated PVT properties at the specified pressure.
        If properties is None, return all available columns except 'pressure'.
        """
        if properties is None:
            properties = [c for c in self.df.columns if c != 'pressure']
        result: Dict[str, Any] = {'pressure': float(pressure)}
        for prop in properties:
            f = self._interp_column(prop)
            result[prop] = f(pressure)
        return result

    def resample(self, pressures: List[float]) -> pd.DataFrame:
        """
        Return a DataFrame with interpolated properties for each pressure in list.
        """
        pressures = np.asarray(pressures, dtype=float)
        rows = []
        for p in pressures:
            rows.append(self.get_properties(float(p)))
        return pd.DataFrame(rows)

    @staticmethod
    def detect_and_parse(input_data: Union[str, io.StringIO, Dict, List]) -> "PVTParser":
        """
        Heuristic to detect data format and create a parser:
        - If input is dict/list -> from_json
        - If input is a string: try JSON, CSV, or plain text table
        """
        if isinstance(input_data, (dict, list)):
            return PVTParser.from_json(input_data)
        if isinstance(input_data, io.StringIO):
            s = input_data.getvalue()
        elif isinstance(input_data, str):
            s = input_data.strip()
        else:
            # unknown type; attempt to pass to pandas
            try:
                return PVTParser.from_csv(input_data)
            except Exception:
                raise ValueError("Unsupported input type")
        # try JSON
        try:
            parsed = json.loads(s)
            return PVTParser.from_json(parsed)
        except Exception:
            pass
        # try CSV
        try:
            # If it contains commas or newlines with consistent columns, treat as CSV
            if ',' in s or ';' in s or '\t' in s:
                return PVTParser.from_csv(s)
        except Exception:
            pass
        # fallback: text table
        return PVTParser.from_text_table(s)

# If this module is executed directly, provide a tiny self-test routine
if __name__ == "__main__":
    sample = """Pressure Rs Bo Viscosity
    1000 200 1.23 0.5
    1500 250 1.18 0.45
    2000 300 1.12 0.42
    2500 340 1.08 0.40
    """
    parser = PVTParser.from_text_table(sample)
    print("DataFrame:")
    print(parser.df)
    print("Interpolated at 1750 psi:")
    print(parser.get_properties(1750))