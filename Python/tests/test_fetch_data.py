import pandas as pd
import pytest

import vwap_orb_pullback
from vwap_orb_pullback import fetch_data


def _make_yf_response(n=30):
    dates = pd.date_range("2024-01-02 09:30:00", periods=n, freq="1min", tz="America/New_York")
    return pd.DataFrame(
        {
            ("Open", "SPY"): [100.0] * n,
            ("High", "SPY"): [101.0] * n,
            ("Low", "SPY"): [99.0] * n,
            ("Close", "SPY"): [100.5] * n,
            ("Volume", "SPY"): [50000] * n,
        },
        index=dates,
    )


def test_fetch_data_returns_required_columns(monkeypatch):
    monkeypatch.setattr(vwap_orb_pullback.yf, "download", lambda **_: _make_yf_response())

    df = fetch_data(symbol="SPY", period="5d", interval="1m")

    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]


def test_fetch_data_drops_na_rows(monkeypatch):
    raw = _make_yf_response(5)
    raw.iloc[2] = None
    monkeypatch.setattr(vwap_orb_pullback.yf, "download", lambda **_: raw)

    df = fetch_data()

    assert df.isna().sum().sum() == 0


def test_fetch_data_raises_on_empty_response(monkeypatch):
    monkeypatch.setattr(
        vwap_orb_pullback.yf,
        "download",
        lambda **_: pd.DataFrame(),
    )

    with pytest.raises(RuntimeError, match="No data returned"):
        fetch_data(symbol="FAKE")


def test_fetch_data_handles_flat_columns(monkeypatch):
    n = 10
    dates = pd.date_range("2024-01-02 09:30:00", periods=n, freq="1min")
    flat = pd.DataFrame(
        {
            "Open": [10.0] * n,
            "High": [11.0] * n,
            "Low": [9.0] * n,
            "Close": [10.5] * n,
            "Volume": [1000] * n,
        },
        index=dates,
    )
    monkeypatch.setattr(vwap_orb_pullback.yf, "download", lambda **_: flat)

    df = fetch_data()

    assert "close" in df.columns
    assert len(df) == n
