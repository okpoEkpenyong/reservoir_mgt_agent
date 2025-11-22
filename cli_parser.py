import os
import sys

# When running this file directly (python cli_parser.py ...), the parent
# directory of the package needs to be on `sys.path` so imports like
# `reservoir_mgt_agent.parsers` resolve. When installed or run as a module
# (`python -m reservoir_mgt_agent.cli_parser`) this is not required.
if __name__ == "__main__" and __package__ is None:
    parent = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if parent not in sys.path:
        sys.path.insert(0, parent)

import click
from reservoir_mgt_agent.parsers.deck_parser import DeckParser
from reservoir_mgt_agent.agent.reservoir_agent import ReservoirAgent

@click.command()
@click.argument("deckfile")
def main(deckfile):
    parser = DeckParser(deckfile)
    agent = ReservoirAgent()

    result = agent.analyze_deck(parser)

    click.echo("=== QC Issues ===")
    for i in result["qc_issues"]:
        click.echo(f"- {i}")

    click.echo("\n=== PLAN ===")
    for p in result["plan"]:
        click.echo(f"- {p}")

if __name__ == "__main__":
    main()
