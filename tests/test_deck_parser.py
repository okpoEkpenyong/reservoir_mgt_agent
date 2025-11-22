"""Unit tests for the DeckParser class in reservoir_mgt_agent.parsers.deck_parser."""

from reservoir_mgt_agent.parsers.deck_parser import DeckParser

def test_extract_sections():
    from pathlib import Path
    example_path = Path(__file__).resolve().parents[1] / "examples" / "example_deck.DATA"
    parser = DeckParser(str(example_path))
    sections = parser.extract_sections()

    assert "RUNSPEC" in sections
    assert "GRID" in sections
    assert "PROPS" in sections
    assert "SCHEDULE" in sections
