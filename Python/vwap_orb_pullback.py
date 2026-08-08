import json
from pathlib import Path

import pandas as pd
import yfinance as yf

from strategy import VwapOrbPullbackStrategy


DEFAULT_CONFIG = {
    "symbol": "SPY",
    "timeframe": "1m",
    "capital": 30000.0,
    "or_minutes": 15,
    "risk_reward": 1.5,
    "use_vwap": True,
    "ema_length": 9,
    "atr_length": 14,
    "market": {
        "timezone": "America/New_York",
    },
    "market_open_hour": 9,
    "market_open_minute": 30,
}


def load_config():
    config_path = Path(__file__).with_name("config.json")
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()

    with config_path.open("r", encoding="utf-8") as config_file:
        user_config = json.load(config_file)

    config = DEFAULT_CONFIG.copy()
    config.update(user_config)
    return config


CONFIG = load_config()
SYMBOL = CONFIG["symbol"]
TIMEFRAME = CONFIG["timeframe"]
CAPITAL = float(CONFIG["capital"])


def fetch_data(symbol=SYMBOL, period="5d", interval=TIMEFRAME):
    data = yf.download(
        tickers=symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )
    if data.empty:
        raise RuntimeError(f"No data returned for {symbol}")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [c[0].lower() for c in data.columns]
    else:
        data.columns = [str(c).lower() for c in data.columns]

    df = data.reset_index().rename(columns={"Datetime": "timestamp", "Date": "timestamp"})
    if "timestamp" not in df.columns:
        df = df.rename(columns={df.columns[0]: "timestamp"})

    return df[["timestamp", "open", "high", "low", "close", "volume"]].dropna()


class OrbBacktestRunner:
    def __init__(self, config):
        self.config = config
        self.strategy = VwapOrbPullbackStrategy(config)

    def run(self, df):
        print(f"Running VWAP ORB Pullback on {len(df)} candles...")
        for i in range(1, len(df)):
            window = df.iloc[: i + 1]
            signal = self.strategy.evaluate_latest(window)
            if signal is None:
                continue

            price = float(signal["price"])
            qty = max(int(CAPITAL / max(price, 0.01)), 1)
            print(
                f"{signal['timestamp']}: {signal['action']} @ {price:.2f}, qty {qty}, "
                f"pos={self.strategy.position}, stop={self.strategy.stop_price:.2f}, "
                f"target={self.strategy.target_price:.2f}"
            )


if __name__ == "__main__":
    bars = fetch_data()
    OrbBacktestRunner(CONFIG).run(bars)
