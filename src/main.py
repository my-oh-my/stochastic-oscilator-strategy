"""Main entry point for the application."""

import argparse
from src.stochastic_processing import run


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stochastic Strategy")
    parser.add_argument(
        "--symbol",
        nargs="+",
        required=True,
        help="Symbols to fetch data for.",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="1d",
        help="Time period to fetch data for (e.g., '1d', '1mo', '1y').",
    )
    parser.add_argument(
        "--intervals",
        type=str,
        default="1h",
        help="Comma-separated list of intervals (e.g., '1m,5m,1h').",
    )
    args = parser.parse_args()
    run(args)
