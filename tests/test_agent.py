"""Tests for the ReservoirAgent analyzing example deck files."""

from reservoir_mgt_agent.parsers.deck_parser import DeckParser
from reservoir_mgt_agent.agent.reservoir_agent import ReservoirAgent


def test_agent_plan():
    """Test that analyzing an example deck returns sections, QC issues, and a plan."""
    from pathlib import Path
    example_path = Path(__file__).resolve().parents[1] / "examples" / "example_deck.DATA"
    parser = DeckParser(str(example_path))
    agent = ReservoirAgent()

    result = agent.analyze_deck(parser)

    assert "sections" in result
    assert "qc_issues" in result
    assert "plan" in result
