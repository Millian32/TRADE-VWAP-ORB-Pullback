import pandas as pd

from strategy import VwapOrbPullbackStrategy


BASE_CONFIG = {
    "or_minutes": 15,
    "risk_reward": 1.5,
    "use_vwap": True,
    "ema_length": 9,
    "atr_length": 14,
    "market": {"timezone": "America/New_York"},
    "market_open_hour": 9,
    "market_open_minute": 30,
}


def make_frame(prev_row, curr_row):
    rows = []
    for index in range(23):
        rows.append(
            {
                "timestamp": f"2024-01-02 09:{index:02d}:00",
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 100.0,
            }
        )

    rows.append(prev_row)
    rows.append(curr_row)
    return pd.DataFrame(rows)


def test_evaluate_latest_returns_none_for_short_series():
    strategy = VwapOrbPullbackStrategy(BASE_CONFIG)
    df = pd.DataFrame([{"timestamp": "t", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}])

    assert strategy.evaluate_latest(df) is None


def test_evaluate_latest_enters_long_after_or(monkeypatch):
    strategy = VwapOrbPullbackStrategy(BASE_CONFIG)
    df = make_frame(
        {
            "timestamp": "2024-01-02 09:54:00",
            "open": 99.0,
            "high": 101.0,
            "low": 98.0,
            "close": 100.0,
            "volume": 100.0,
        },
        {
            "timestamp": "2024-01-02 10:00:00",
            "open": 100.0,
            "high": 103.0,
            "low": 99.0,
            "close": 102.0,
            "volume": 200.0,
        },
    )

    enriched = df.copy()
    enriched["market_ts"] = pd.to_datetime(enriched["timestamp"]).dt.tz_localize("America/New_York")
    enriched["or_end_time"] = pd.Timestamp("2024-01-02 09:45:00", tz="America/New_York")
    enriched["or_high"] = 101.0
    enriched["or_low"] = 95.0
    enriched["vwap"] = 100.0
    enriched["ema9"] = 100.0
    enriched["atr"] = 2.0

    monkeypatch.setattr(strategy, "add_indicators", lambda incoming: enriched)

    signal = strategy.evaluate_latest(df)

    assert signal["action"] == "enter_long"
    assert strategy.position == 1
    assert strategy.stop_price == 100.0
    assert strategy.target_price == 105.0


def test_evaluate_latest_returns_none_during_opening_range(monkeypatch):
    strategy = VwapOrbPullbackStrategy(BASE_CONFIG)
    df = make_frame(
        {
            "timestamp": "2024-01-02 09:34:00",
            "open": 99.0,
            "high": 101.0,
            "low": 98.0,
            "close": 100.0,
            "volume": 100.0,
        },
        {
            "timestamp": "2024-01-02 09:40:00",
            "open": 100.0,
            "high": 104.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 200.0,
        },
    )

    enriched = df.copy()
    enriched["market_ts"] = pd.to_datetime(enriched["timestamp"]).dt.tz_localize("America/New_York")
    enriched["or_end_time"] = pd.Timestamp("2024-01-02 09:45:00", tz="America/New_York")
    enriched["or_high"] = 101.0
    enriched["or_low"] = 95.0
    enriched["vwap"] = 100.0
    enriched["ema9"] = 100.0
    enriched["atr"] = 2.0

    monkeypatch.setattr(strategy, "add_indicators", lambda incoming: enriched)

    assert strategy.evaluate_latest(df) is None


def test_evaluate_latest_exits_long_on_stop(monkeypatch):
    strategy = VwapOrbPullbackStrategy(BASE_CONFIG)
    strategy.position = 1
    strategy.entry_price = 102.0
    strategy.stop_price = 100.0
    strategy.target_price = 105.0

    df = make_frame(
        {
            "timestamp": "2024-01-02 09:59:00",
            "open": 102.0,
            "high": 103.0,
            "low": 101.0,
            "close": 102.0,
            "volume": 100.0,
        },
        {
            "timestamp": "2024-01-02 10:00:00",
            "open": 101.0,
            "high": 102.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 200.0,
        },
    )

    enriched = df.copy()
    enriched["market_ts"] = pd.to_datetime(enriched["timestamp"]).dt.tz_localize("America/New_York")
    enriched["or_end_time"] = pd.Timestamp("2024-01-02 09:45:00", tz="America/New_York")
    enriched["or_high"] = 101.0
    enriched["or_low"] = 95.0
    enriched["vwap"] = 100.0
    enriched["ema9"] = 100.0
    enriched["atr"] = 2.0

    monkeypatch.setattr(strategy, "add_indicators", lambda incoming: enriched)

    signal = strategy.evaluate_latest(df)

    assert signal["action"] == "exit_long"
    assert signal["price"] == 100.0
    assert strategy.position == 0


def test_evaluate_latest_enters_short_without_vwap_filter(monkeypatch):
    config = BASE_CONFIG.copy()
    config["use_vwap"] = False
    strategy = VwapOrbPullbackStrategy(config)
    df = make_frame(
        {
            "timestamp": "2024-01-02 09:59:00",
            "open": 98.0,
            "high": 99.0,
            "low": 97.0,
            "close": 98.0,
            "volume": 100.0,
        },
        {
            "timestamp": "2024-01-02 10:00:00",
            "open": 97.0,
            "high": 98.0,
            "low": 92.0,
            "close": 94.0,
            "volume": 200.0,
        },
    )

    enriched = df.copy()
    enriched["market_ts"] = pd.to_datetime(enriched["timestamp"]).dt.tz_localize("America/New_York")
    enriched["or_end_time"] = pd.Timestamp("2024-01-02 09:45:00", tz="America/New_York")
    enriched["or_high"] = 101.0
    enriched["or_low"] = 95.0
    enriched["vwap"] = 90.0
    enriched["ema9"] = 96.0
    enriched["atr"] = 2.0

    monkeypatch.setattr(strategy, "add_indicators", lambda incoming: enriched)

    signal = strategy.evaluate_latest(df)

    assert signal["action"] == "enter_short"
    assert strategy.position == -1
    assert strategy.stop_price == 96.0
    assert strategy.target_price == 91.0
