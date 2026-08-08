import pandas as pd
import ta
from zoneinfo import ZoneInfo


class VwapOrbPullbackStrategy:
    def __init__(self, config):
        self.config = config
        self.market_tz = ZoneInfo(config.get("market", {}).get("timezone", "America/New_York"))
        self.or_minutes = int(config.get("or_minutes", 15))
        self.market_open_hour = int(config.get("market_open_hour", 9))
        self.market_open_minute = int(config.get("market_open_minute", 30))
        self.risk_reward = float(config.get("risk_reward", 1.5))
        self.use_vwap = bool(config.get("use_vwap", True))
        self.ema_length = int(config.get("ema_length", 9))
        self.atr_length = int(config.get("atr_length", 14))

        self.position = 0
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.target_price = 0.0

    def _to_market_timestamp(self, timestamp):
        parsed = pd.Timestamp(timestamp)
        if parsed.tzinfo is None:
            return parsed.tz_localize(self.market_tz)
        return parsed.tz_convert(self.market_tz)

    def _apply_opening_range_levels(self, data):
        data["or_high"] = pd.NA
        data["or_low"] = pd.NA
        data["or_end_time"] = None

        grouped = data.groupby(data["market_ts"].dt.date, sort=False)
        for _, day_frame in grouped:
            idx = day_frame.index
            first_ts = day_frame.iloc[0]["market_ts"]
            session_start = pd.Timestamp(
                year=first_ts.year,
                month=first_ts.month,
                day=first_ts.day,
                hour=self.market_open_hour,
                minute=self.market_open_minute,
                tz=self.market_tz,
            )
            or_end_time = session_start + pd.Timedelta(minutes=self.or_minutes)
            in_opening_range = (day_frame["market_ts"] >= session_start) & (day_frame["market_ts"] <= or_end_time)

            if in_opening_range.any():
                or_high = float(day_frame.loc[in_opening_range, "high"].max())
                or_low = float(day_frame.loc[in_opening_range, "low"].min())
                data.loc[idx, "or_high"] = or_high
                data.loc[idx, "or_low"] = or_low
                data.loc[idx, "or_end_time"] = or_end_time

        data["or_high"] = pd.to_numeric(data["or_high"], errors="coerce")
        data["or_low"] = pd.to_numeric(data["or_low"], errors="coerce")
        return data

    def add_indicators(self, df):
        data = df.copy()
        data["market_ts"] = data["timestamp"].apply(self._to_market_timestamp)

        data["vwap"] = ta.volume.VolumeWeightedAveragePrice(
            data["high"], data["low"], data["close"], data["volume"]
        ).volume_weighted_average_price()
        data["ema9"] = ta.trend.EMAIndicator(data["close"], window=self.ema_length).ema_indicator()
        data["atr"] = ta.volatility.AverageTrueRange(
            data["high"], data["low"], data["close"], window=self.atr_length
        ).average_true_range()

        return self._apply_opening_range_levels(data)

    def _reset_position(self):
        self.position = 0
        self.entry_price = 0.0
        self.stop_price = 0.0
        self.target_price = 0.0

    def evaluate_latest(self, df):
        min_bars = max(25, self.atr_length + 2)
        if len(df) < min_bars:
            return None

        data = self.add_indicators(df)
        curr = data.iloc[-1]

        if pd.isna(curr["or_high"]) or pd.isna(curr["or_low"]) or pd.isna(curr["or_end_time"]):
            return None
        if pd.isna(curr["vwap"]) or pd.isna(curr["ema9"]) or pd.isna(curr["atr"]):
            return None

        price = float(curr["close"])
        timestamp = str(curr["timestamp"])
        after_or_window = curr["market_ts"] > curr["or_end_time"]

        if self.position == 1:
            stop_hit = float(curr["low"]) <= self.stop_price
            target_hit = float(curr["high"]) >= self.target_price
            if stop_hit or target_hit:
                exit_price = self.stop_price if stop_hit else self.target_price
                self._reset_position()
                return {
                    "action": "exit_long",
                    "price": float(exit_price),
                    "timestamp": timestamp,
                }

        if self.position == -1:
            stop_hit = float(curr["high"]) >= self.stop_price
            target_hit = float(curr["low"]) <= self.target_price
            if stop_hit or target_hit:
                exit_price = self.stop_price if stop_hit else self.target_price
                self._reset_position()
                return {
                    "action": "exit_short",
                    "price": float(exit_price),
                    "timestamp": timestamp,
                }

        breakout_long = price > float(curr["or_high"])
        breakout_short = price < float(curr["or_low"])

        if self.use_vwap:
            pullback_long = price > float(curr["vwap"]) and price > float(curr["ema9"]) and float(curr["low"]) <= float(curr["vwap"])
            pullback_short = price < float(curr["vwap"]) and price < float(curr["ema9"]) and float(curr["high"]) >= float(curr["vwap"])
        else:
            pullback_long = price > float(curr["ema9"])
            pullback_short = price < float(curr["ema9"])

        long_condition = after_or_window and breakout_long and pullback_long
        short_condition = after_or_window and breakout_short and pullback_short

        atr = float(curr["atr"])
        if long_condition and self.position <= 0:
            self.position = 1
            self.entry_price = price
            self.stop_price = price - atr
            self.target_price = price + (atr * self.risk_reward)
            return {
                "action": "enter_long",
                "price": price,
                "timestamp": timestamp,
            }

        if short_condition and self.position >= 0:
            self.position = -1
            self.entry_price = price
            self.stop_price = price + atr
            self.target_price = price - (atr * self.risk_reward)
            return {
                "action": "enter_short",
                "price": price,
                "timestamp": timestamp,
            }

        return None
