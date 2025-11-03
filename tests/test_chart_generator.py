"""Unit tests for the chart_generator module."""

from unittest.mock import MagicMock, patch

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.chart_generator import (
    _add_colored_ranges,
    _parse_interval_to_minutes,
    generate_stochastic_chart,
)


@pytest.mark.parametrize(
    "interval_str, expected_minutes",
    [
        ("1m", 1),
        ("5m", 5),
        ("1h", 60),
        ("4h", 240),
        ("1d", 1440),
        ("1wk", 10080),
    ],
)
def test_parse_interval_to_minutes_valid(interval_str, expected_minutes):
    """Test that _parse_interval_to_minutes converts valid interval strings correctly."""
    assert _parse_interval_to_minutes(interval_str) == expected_minutes


@pytest.mark.parametrize(
    "invalid_interval",
    ["1y", "1s", "abc", "1", "1M"],
)
def test_parse_interval_to_minutes_invalid(invalid_interval):
    """Test that _parse_interval_to_minutes raises ValueError for invalid inputs."""
    with pytest.raises(ValueError):
        _parse_interval_to_minutes(invalid_interval)


def test_add_colored_ranges():
    """Test that _add_colored_ranges calls add_vrect with the correct parameters."""
    # Arrange
    fig = MagicMock(spec=go.Figure)
    merged_df = pd.DataFrame(
        {
            "Datetime": pd.to_datetime(
                ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
            ),
            "%K_1h": [85, 50, 15, 50],
            "%K_4h": [90, 50, 10, 50],
        }
    )
    intervals = ["1h", "4h"]

    # Act
    _add_colored_ranges(fig, merged_df, intervals)

    # Assert
    assert fig.add_vrect.call_count == 2
    fig.add_vrect.assert_any_call(
        x0=pd.to_datetime("2023-01-01"),
        x1=pd.to_datetime("2023-01-02"),
        fillcolor="rgba(255, 0, 0, 0.2)",
        layer="below",
        line_width=0,
        row=1,
        col=1,
    )
    fig.add_vrect.assert_any_call(
        x0=pd.to_datetime("2023-01-03"),
        x1=pd.to_datetime("2023-01-04"),
        fillcolor="rgba(0, 255, 0, 0.2)",
        layer="below",
        line_width=0,
        row=1,
        col=1,
    )


def test_add_colored_ranges_last_candle():
    """Test _add_colored_ranges handles conditions on the last candle."""
    # Arrange
    fig = MagicMock(spec=go.Figure)
    merged_df = pd.DataFrame(
        {
            "Datetime": pd.to_datetime(
                ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]
            ),
            "%K_1h": [50, 50, 50, 85],
            "%K_4h": [50, 50, 50, 90],
        }
    )
    intervals = ["1h", "4h"]

    # Act
    _add_colored_ranges(fig, merged_df, intervals)

    # Assert
    fig.add_vrect.assert_called_once_with(
        x0=pd.to_datetime("2023-01-04"),
        x1=pd.to_datetime("2023-01-04"),
        fillcolor="rgba(255, 0, 0, 0.2)",
        layer="below",
        line_width=0,
        row=1,
        col=1,
    )


@patch("src.chart_generator.make_subplots")
def test_generate_stochastic_chart_save_only(mock_make_subplots, tmp_path):
    """Test that generate_stochastic_chart saves the chart when output_dir is provided."""
    # Arrange
    mock_fig = MagicMock()
    mock_make_subplots.return_value = mock_fig
    output_dir = tmp_path / "charts"
    output_dir.mkdir()

    data_dict = {
        "1h": pd.DataFrame(
            {
                "Datetime": pd.to_datetime(["2023-01-01"]),
                "Open": [100],
                "High": [110],
                "Low": [90],
                "Close": [105],
                "%K": [80],
                "%D": [75],
            }
        )
    }

    # Act
    generate_stochastic_chart("BTC/USD", data_dict, output_dir=str(output_dir))

    # Assert
    expected_path = output_dir / "BTC_USD_stochastic_chart.html"
    mock_fig.write_html.assert_called_once_with(str(expected_path))
    mock_fig.show.assert_not_called()


@patch("src.chart_generator.make_subplots")
def test_generate_stochastic_chart_show(mock_make_subplots):
    """Test that generate_stochastic_chart shows the chart when output_dir is None."""
    # Arrange
    mock_fig = MagicMock()
    mock_make_subplots.return_value = mock_fig

    data_dict = {
        "1h": pd.DataFrame(
            {
                "Datetime": pd.to_datetime(["2023-01-01"]),
                "Open": [100],
                "High": [110],
                "Low": [90],
                "Close": [105],
                "%K": [80],
                "%D": [75],
            }
        )
    }

    # Act
    generate_stochastic_chart("BTC-USD", data_dict)

    # Assert
    mock_fig.show.assert_called_once()
    mock_fig.write_html.assert_not_called()


@patch("src.chart_generator.make_subplots")
def test_generate_stochastic_chart_multiple_intervals(mock_make_subplots):
    """Test generate_stochastic_chart with multiple intervals."""
    # Arrange
    mock_fig = MagicMock()
    mock_make_subplots.return_value = mock_fig

    data_dict = {
        "1h": pd.DataFrame(
            {
                "Datetime": pd.to_datetime(["2023-01-01"]),
                "Open": [100],
                "High": [110],
                "Low": [90],
                "Close": [105],
                "%K": [80],
                "%D": [75],
            }
        ),
        "4h": pd.DataFrame(
            {
                "Datetime": pd.to_datetime(["2023-01-01"]),
                "Open": [100],
                "High": [110],
                "Low": [90],
                "Close": [105],
                "%K": [85],
                "%D": [80],
            }
        ),
    }

    # Act
    generate_stochastic_chart("BTC-USD", data_dict)

    # Assert
    assert mock_fig.add_trace.call_count == 5


def test_generate_stochastic_chart_no_data(tmp_path):
    """Test that generate_stochastic_chart handles an empty data_dict gracefully."""
    # Act & Assert (should not raise an error)
    generate_stochastic_chart("BTC-USD", {}, output_dir=str(tmp_path))
