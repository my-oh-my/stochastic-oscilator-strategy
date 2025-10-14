"""Module for calculating stochastic indicators."""

import argparse
import pandas as pd
from ta.momentum import StochasticOscillator
from src.data_fetcher import fetch_market_data


def calculate_stochastic(
    data: pd.DataFrame, k_window: int = 14, d_window: int = 3
) -> pd.DataFrame:
    """Calculates the Stochastic Oscillator for the given data using the 'ta' library."""
    if data is None or data.empty:
        raise ValueError("Input data cannot be empty.")

    if not all(col in data.columns for col in ["High", "Low", "Close"]):
        raise ValueError("Input data must contain 'High', 'Low', and 'Close' columns.")

    stoch = StochasticOscillator(
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        window=k_window,
        smooth_window=d_window,
    )
    data["%K"] = stoch.stoch()
    data["%D"] = stoch.stoch_signal()

    return data


def run(args: argparse.Namespace):
    """Runs the stochastic processing logic."""

    symbol = args.symbol
    intervals = [interval.strip() for interval in args.intervals.split(",")]

    for interval in intervals:
        try:
            print(f"Fetching data for {symbol} with interval {interval}...")
            market_data = fetch_market_data(symbol, args.period, interval)

            print(
                f"Calculating stochastic indicator for {symbol} with interval {interval}..."
            )
            stochastic_data = calculate_stochastic(market_data)

            print(f"Results for {symbol} - {interval}:")
            print(stochastic_data.tail())
            print("\n" + "=" * 80 + "\n")

        except ValueError as e:
            print(f"Error processing {symbol} for interval {interval}: {e}")
