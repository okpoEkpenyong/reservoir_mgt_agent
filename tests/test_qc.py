"""Unit tests for QC functionality in reservoir_mgt_agent."""

from reservoir_mgt_agent.parsers.deck_parser import DeckParser
from reservoir_mgt_agent.qc.rules import run_qc

def test_qc():
    from pathlib import Path
    example_path = Path(__file__).resolve().parents[1] / "examples" / "example_deck.DATA"
    parser = DeckParser(str(example_path))
    sections = parser.extract_sections()

    issues = run_qc(parser.content, sections)

    # Example deck should have no QC errors
    assert len(issues) == 0
