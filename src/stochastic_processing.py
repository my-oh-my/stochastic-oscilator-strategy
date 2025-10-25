"""Module for calculating stochastic indicators."""

import argparse
import pandas as pd
from ta.momentum import StochasticOscillator
from src.chart_generator import generate_stochastic_chart
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


def _check_last_candle_condition(
    stochastic_data_all_intervals: dict[str, pd.DataFrame],
) -> bool:
    """Checks if all stochastics are oversold or overbought on the last candle."""
    last_k_values = []
    for _, data in stochastic_data_all_intervals.items():
        if not data.empty:
            last_k_values.append(data["%K"].iloc[-1])

    if not last_k_values:
        return False

    is_overbought = all(k > 80 for k in last_k_values)
    is_oversold = all(k < 20 for k in last_k_values)

    return is_overbought or is_oversold


def run(args: argparse.Namespace):
    """Runs the stochastic processing logic for a list of symbols."""
    symbols = [symbol.strip() for symbol in args.symbols.split(",")]
    intervals = [interval.strip() for interval in args.intervals.split(",")]

    for symbol in symbols:
        print(f"\nProcessing symbol: {symbol}")
        stochastic_data_all_intervals = {}
        all_intervals_processed = True

        for interval in intervals:
            try:
                print(f"Fetching data for {symbol} with interval {interval}...")
                market_data = fetch_market_data(symbol, args.period, interval)

                print(
                    f"Calculating stochastic indicator for {symbol} with interval {interval}..."
                )
                stochastic_data = calculate_stochastic(
                    market_data, k_window=args.k_window, d_window=args.d_window
                )
                stochastic_data_all_intervals[interval] = stochastic_data

                print(f"Successfully processed interval {interval}.")

            except ValueError as e:
                print(f"Error processing {symbol} for interval {interval}: {e}")
                all_intervals_processed = False
                break  # Stop processing other intervals for this symbol

        if all_intervals_processed and stochastic_data_all_intervals:
            if args.plot_all or _check_last_candle_condition(
                stochastic_data_all_intervals
            ):
                print(f"Condition met for {symbol}. Generating chart...")
                generate_stochastic_chart(
                    symbol, stochastic_data_all_intervals, args.save_html
                )
            else:
                print(f"Condition not met for {symbol}. No chart will be generated.")
