"""Unit tests for the stochastic_processing module."""

import argparse
import pandas as pd
import pytest
from src.stochastic_processing import (
    calculate_stochastic,
    _check_last_candle_condition,
    run,
)


@pytest.fixture
def _sample_market_data() -> pd.DataFrame:
    """Provides a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "High": [
                110,
                112,
                111,
                109,
                108,
                107,
                106,
                105,
                104,
                103,
                102,
                101,
                100,
                99,
                98,
                115,
                112,
                111,
                109,
                108,
            ],
            "Low": [
                100,
                101,
                102,
                103,
                104,
                103,
                102,
                101,
                100,
                99,
                98,
                97,
                96,
                95,
                94,
                99,
                101,
                102,
                103,
                104,
            ],
            "Close": [
                105,
                111,
                103,
                108,
                105,
                106,
                105,
                104,
                103,
                102,
                101,
                100,
                99,
                98,
                97,
                110,
                111,
                103,
                108,
                105,
            ],
        }
    )


def test_calculate_stochastic_success(_sample_market_data):
    """Test successful calculation of the stochastic oscillator."""
    # Arrange
    data = _sample_market_data

    # Act
    result = calculate_stochastic(data, k_window=14, d_window=3)
    print(result)
    # Assert
    assert "%K" in result.columns
    assert "%D" in result.columns
    assert not result["%K"].isnull().all()
    assert not result["%D"].isnull().all()

    # Check the last values
    pd.testing.assert_series_equal(
        result[["%K", "%D"]].iloc[-1],
        pd.Series({"%K": 52.380952, "%D": 53.968254}),
        check_names=False,
        atol=1e-6,
    )


def test_calculate_stochastic_empty_data():
    """Test ValueError when input data is empty."""
    # Arrange
    empty_df = pd.DataFrame()

    # Act & Assert
    with pytest.raises(ValueError, match="Input data cannot be empty."):
        calculate_stochastic(empty_df)


def test_calculate_stochastic_missing_columns():
    """Test ValueError when required columns are missing."""
    # Arrange
    data = pd.DataFrame({"Open": [1, 2, 3]})

    # Act & Assert
    with pytest.raises(
        ValueError, match="Input data must contain 'High', 'Low', and 'Close' columns."
    ):
        calculate_stochastic(data)


@pytest.mark.parametrize(
    "k_values, expected",
    [
        ([81, 85], True),  # All overbought
        ([10, 15], True),  # All oversold
        ([50, 60], False),  # Neither
        ([81, 50], False),  # Mixed
        ([10, 50], False),  # Mixed
        ([], False),  # Empty
    ],
)
def test_check_last_candle_condition(k_values, expected):
    """Test the _check_last_candle_condition function with various inputs."""
    # Arrange
    stochastic_data = {
        f"interval_{i}": pd.DataFrame({"%K": [k]}) for i, k in enumerate(k_values)
    }

    # Act
    result = _check_last_candle_condition(stochastic_data)

    # Assert
    assert result is expected


def test_check_last_candle_condition_empty_dataframe():
    """Test with a dictionary containing an empty DataFrame."""
    stochastic_data = {"1h": pd.DataFrame({"%K": []})}
    assert _check_last_candle_condition(stochastic_data) is False


def test_run_condition_met_generates_chart(mocker):
    """Test that `run` generates a chart when conditions are met."""
    # Arrange
    mock_fetch = mocker.patch("src.stochastic_processing.fetch_market_data")
    mock_generate = mocker.patch("src.stochastic_processing.generate_stochastic_chart")
    mock_fetch.return_value = pd.DataFrame(
        {
            "High": [110],
            "Low": [100],
            "Close": [105],
            "Datetime": [pd.to_datetime("2023-01-01")],
        }
    )

    # Mocking calculate_stochastic to return a controlled output
    mocker.patch(
        "src.stochastic_processing.calculate_stochastic",
        return_value=pd.DataFrame({"%K": [85], "%D": [82]}),
    )

    args = argparse.Namespace(
        symbols="BTC-USD",
        intervals="1h",
        period="1d",
        save_html=False,
        plot_all=False,
        k_window=14,
        d_window=3,
        save_html_dir=None,
    )

    # Act
    run(args)

    # Assert
    mock_generate.assert_called_once()


def test_run_condition_not_met_no_chart(mocker):
    """Test that `run` does not generate a chart when conditions are not met."""
    # Arrange
    mock_fetch = mocker.patch("src.stochastic_processing.fetch_market_data")
    mock_generate = mocker.patch("src.stochastic_processing.generate_stochastic_chart")
    mock_fetch.return_value = pd.DataFrame(
        {
            "High": [110],
            "Low": [100],
            "Close": [105],
            "Datetime": [pd.to_datetime("2023-01-01")],
        }
    )

    mocker.patch(
        "src.stochastic_processing.calculate_stochastic",
        return_value=pd.DataFrame({"%K": [50], "%D": [50]}),
    )

    args = argparse.Namespace(
        symbols="BTC-USD",
        intervals="1h",
        period="1d",
        save_html=False,
        plot_all=False,
        k_window=14,
        d_window=3,
    )

    # Act
    run(args)

    # Assert
    mock_generate.assert_not_called()


def test_run_plot_all_generates_chart(mocker):
    """Test `run` generates a chart with --plot-all, even if conditions not met."""
    # Arrange
    mock_fetch = mocker.patch("src.stochastic_processing.fetch_market_data")
    mock_generate = mocker.patch("src.stochastic_processing.generate_stochastic_chart")
    mock_fetch.return_value = pd.DataFrame(
        {
            "High": [110],
            "Low": [100],
            "Close": [105],
            "Datetime": [pd.to_datetime("2023-01-01")],
        }
    )

    mocker.patch(
        "src.stochastic_processing.calculate_stochastic",
        return_value=pd.DataFrame({"%K": [50], "%D": [50]}),
    )

    args = argparse.Namespace(
        symbols="BTC-USD",
        intervals="1h",
        period="1d",
        save_html=False,
        plot_all=True,  # Key change here
        k_window=14,
        d_window=3,
        save_html_dir=None,
    )

    # Act
    run(args)

    # Assert
    mock_generate.assert_called_once()


def test_run_fetch_error_no_chart(mocker):
    """Test that `run` handles fetch errors gracefully and does not generate a chart."""
    # Arrange
    mock_fetch = mocker.patch("src.stochastic_processing.fetch_market_data")
    mock_generate = mocker.patch("src.stochastic_processing.generate_stochastic_chart")
    mock_fetch.side_effect = ValueError("Test error")

    args = argparse.Namespace(
        symbols="BTC-USD",
        intervals="1h",
        period="1d",
        save_html=False,
        plot_all=False,
        k_window=14,
        d_window=3,
    )

    # Act
    run(args)

    # Assert
    mock_generate.assert_not_called()
