"""Module for generating charts."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _parse_interval_to_minutes(interval_str: str) -> int:
    """Converts an interval string (e.g., '1m', '1h', '1d', '1wk', '1mo') to minutes."""
    unit_map = {"m": 1, "h": 60, "d": 24 * 60, "wk": 7 * 24 * 60}

    # Sort units by length, descending, to handle 'wk' before 'k' if 'k' were a unit.
    sorted_units = sorted(unit_map.keys(), key=len, reverse=True)

    for unit in sorted_units:
        if interval_str.endswith(unit):
            value_str = interval_str[: -len(unit)]
            if value_str.isdigit():
                return int(value_str) * unit_map[unit]

    raise ValueError(f"Unknown or invalid interval format: {interval_str}")


def _add_colored_ranges(
    fig: go.Figure,
    merged_df: pd.DataFrame,
    intervals: list[str],
):
    """Adds colored vertical ranges to the candlestick chart in an optimized way."""

    # Vectorized conditions for better performance
    overbought_conditions = [merged_df[f"%K_{interval}"] > 80 for interval in intervals]
    oversold_conditions = [merged_df[f"%K_{interval}"] < 20 for interval in intervals]

    all_overbought = pd.concat(overbought_conditions, axis=1).all(axis=1)
    all_oversold = pd.concat(oversold_conditions, axis=1).all(axis=1)

    # Helper function to find consecutive ranges and add a single rectangle for each
    def find_and_add_ranges(condition, color):
        # Find indices where the condition starts and ends
        starts = merged_df.index[condition & ~condition.shift(fill_value=False)]
        ends = merged_df.index[condition & ~condition.shift(-1, fill_value=False)]

        for start, end in zip(starts, ends):
            x0 = merged_df.loc[start, "Datetime"]

            # The end of the range should be the start of the next candle
            end_iloc = merged_df.index.get_loc(end)
            if end_iloc + 1 < len(merged_df):
                x1 = merged_df["Datetime"].iloc[end_iloc + 1]
            else:
                # For the last candle in the dataframe, we can't get the next candle's start time.
                # We'll use the current candle's start time, creating a zero-width rectangle,
                # which is consistent with the original implementation's behavior for the last point.
                x1 = merged_df.loc[end, "Datetime"]

            fig.add_vrect(
                x0=x0,
                x1=x1,
                fillcolor=color,
                layer="below",
                line_width=0,
                row=1,
                col=1,
            )

    find_and_add_ranges(all_overbought, "rgba(255, 0, 0, 0.2)")
    find_and_add_ranges(all_oversold, "rgba(0, 255, 0, 0.2)")


def generate_stochastic_chart(
    symbol: str, data_dict: dict[str, pd.DataFrame], save_only: bool = False
):
    """Generates and either saves or displays a stochastic chart with a candlestick subplot.

    Args:
        symbol: The market symbol (e.g., "BTC-USD").
        data_dict: A dictionary where keys are intervals (e.g., "1h")
                   and values are DataFrames with stochastic data.
        save_only: If True, saves the chart as an HTML file.
                   If False, opens the chart in a web browser.
    """
    if not data_dict:
        print("No data to plot.")
        return

    # Find the lowest interval for the candlestick chart
    lowest_interval = min(data_dict.keys(), key=_parse_interval_to_minutes)
    candlestick_data = data_dict[lowest_interval].copy()

    # Merge dataframes
    merged_df = candlestick_data
    sorted_intervals = sorted(data_dict.keys(), key=_parse_interval_to_minutes)

    for interval in sorted_intervals:
        if interval == lowest_interval:
            merged_df.rename(
                columns={"%K": f"%K_{interval}", "%D": f"%D_{interval}"}, inplace=True
            )
        else:
            data_to_merge = data_dict[interval][["Datetime", "%K", "%D"]].copy()
            data_to_merge.rename(
                columns={"%K": f"%K_{interval}", "%D": f"%D_{interval}"}, inplace=True
            )
            merged_df = pd.merge_asof(
                merged_df,
                data_to_merge,
                on="Datetime",
                direction="backward",
            )

    # Create subplots
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
    )

    # Candlestick chart for the lowest interval
    fig.add_trace(
        go.Candlestick(
            x=candlestick_data["Datetime"],
            open=candlestick_data["Open"],
            high=candlestick_data["High"],
            low=candlestick_data["Low"],
            close=candlestick_data["Close"],
            name=f"Candlestick ({lowest_interval})",
        ),
        row=1,
        col=1,
    )

    # Stochastic oscillators for all intervals
    for interval, data in data_dict.items():
        fig.add_trace(
            go.Scatter(
                x=data["Datetime"],
                y=data["%K"],
                mode="lines",
                name=f"%K ({interval})",
                line={"width": 2},
            ),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=data["Datetime"],
                y=data["%D"],
                mode="lines",
                name=f"%D ({interval})",
                line={"width": 1, "dash": "dash"},
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        title_text=f"Stochastic Oscillator and Candlestick Chart for {symbol}",
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        legend_title="Indicators",
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Stochastic Value", row=2, col=1)

    # Add horizontal lines for overbought and oversold levels to the second subplot
    fig.add_hline(
        y=80,
        line_dash="dot",
        line_color="red",
        annotation_text="Overbought",
        row=2,
        col=1,
    )
    fig.add_hline(
        y=20,
        line_dash="dot",
        line_color="green",
        annotation_text="Oversold",
        row=2,
        col=1,
    )

    _add_colored_ranges(fig, merged_df, list(data_dict.keys()))

    if save_only:
        chart_filename = f"{symbol.replace('/', '_')}_stochastic_chart.html"
        fig.write_html(chart_filename)
        print(f"Chart saved to {chart_filename}")
    else:
        fig.show()
