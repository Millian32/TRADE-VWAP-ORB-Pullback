# TRADE-VWAP-ORB-Pullback

This strategy is an Opening Range Breakout pullback system that uses the first X minutes after the market open to define the opening range, then looks for breakout entries that pull back to VWAP for confirmation. It is designed to trade in the direction of momentum after the opening range is established, with ATR-based stop loss and profit target levels.

How it works
It records the opening range high and low during the first part of the session after the U.S. market opens at 9:30 AM New York time.

After the opening range period ends, it waits for price to break above the opening range high for longs or break below the opening range low for shorts.

For a long trade, price must also be above VWAP and the 9 EMA, and the candle must pull back to VWAP before entry.

For a short trade, price must be below VWAP and the 9 EMA, and the candle must retest VWAP from below before entry.

Risk management uses ATR(14) to set the stop loss and take profit automatically.

How to use it
Add the strategy to a chart on TradingView.
Use it on intraday timeframes such as 1-minute, 5-minute, or 15-minute charts.
Focus on liquid, trend-sensitive markets like large-cap stocks, futures, or ETFs.
Watch for the opening range to form after the market open.
After the opening range ends, the strategy will only trigger when breakout and pullback conditions align.

Settings explained
Opening Range Minutes
This controls how long the opening range lasts after the market opens.
Lower values, like 5 or 15, create a tighter opening range.
Higher values create a wider range and fewer signals.

Risk/Reward Ratio
This sets the profit target as a multiple of ATR.
A value of 1.5 means the target is 1.5 times ATR away from entry.
Higher values aim for bigger winners but may reduce win rate.

Use VWAP Filter
This toggles the VWAP condition on or off.
Enabled: trades require price confirmation around VWAP.
Disabled: the strategy still uses the opening range breakout logic, but removes VWAP as an extra filter.

Trading behavior
This strategy is meant to catch early-session momentum while avoiding low-quality breakout entries. The VWAP and EMA filters help confirm trend direction, while the pullback requirement is intended to improve entry quality instead of chasing extended moves. The ATR stop and target make the strategy adaptive to volatility.

Suggested description for TradingView
VWAP ORB Pullback Strategy combines the opening range breakout with VWAP and EMA pullback confirmation. It defines the opening range during the first user-defined minutes after the market open, then looks for price to break that range and retest VWAP before entering. Long trades require price above VWAP and the 9 EMA, while short trades require price below both. Exits are managed with ATR-based stop loss and take profit levels using the selected risk/reward ratio.

Python Auto-Trader

The Python app now supports automated signal evaluation and broker execution through a pluggable broker interface.

Files:
- Python/auto_trader.py: main loop that polls market data, evaluates strategy, and sends orders.
- Python/strategy.py: VWAP ORB pullback signal engine.
- Python/broker.py: broker abstraction with `PaperBroker`, `AlpacaBroker`, and `IbkrBroker`.
- Python/config.json: strategy and broker configuration.
- Python/vwap_orb_pullback.py: standalone fetch-and-evaluate script for quick local signal checks.

Quick start (paper mode):
1. `cd Python`
2. `python -m venv .venv`
3. `.venv\Scripts\activate`
4. `pip install -r requirements.txt`
5. Ensure `config.json` has `"broker": { "name": "paper" }` and `"dry_run": true`
6. `python auto_trader.py`

One-command setup and dry-run:
- Setup once: `./setup.ps1`
- Start paper dry-run trader: `./run_paper_dry_run.ps1`
- Optional quick smoke run (one processed bar): `./run_paper_dry_run.ps1 -MaxLoops 1`

Risk, session, and journaling controls:
- `risk.max_drawdown_pct`: blocks new entries after portfolio drawdown breaches the limit.
- `risk.max_trades_per_day`: blocks new entries after the daily entry count is reached.
- `risk.kill_switch_file`: if this file exists, all new entries are blocked immediately.
- `market.calendar` and `market.timezone`: use exchange hours and holidays to avoid trading when the market is closed.
- `logging.path`: JSONL structured event log.
- `trade_journal.format`: `csv` or `sqlite`.

Alpaca integration:
1. Copy `Python/config.local.example.json` to `Python/config.local.json` and set broker mode to Alpaca paper.
2. In `Python/config.local.json`, set:
	- `"dry_run": false`
	- `"broker": { "name": "alpaca", "paper": true, "alpaca_base_url": "https://paper-api.alpaca.markets/v2" }`
	- `"market_data": { "source": "alpaca", "alpaca_base_url": "https://data.alpaca.markets", "alpaca_feed": "iex" }`
3. Set credentials on this PC with the helper script:
	- `cd Python`
	- `./set_alpaca_env.ps1`
	- Enter `ALPACA_API_KEY` and `ALPACA_API_SECRET` when prompted.
4. Run the trader:
	- `./.venv/Scripts/python.exe auto_trader.py`

IBKR integration:
1. Start TWS or IB Gateway locally.
2. In `config.json`, set `"broker": { "name": "ibkr", "ibkr_host": "127.0.0.1", "ibkr_port": 7497, "ibkr_client_id": 1, "ibkr_exchange": "SMART", "ibkr_currency": "USD" }`
3. For paper trading, use your IBKR paper TWS or Gateway port.
4. Set `"dry_run": false` to send orders.
5. Run `python auto_trader.py`

Safety notes:
- Start with `dry_run: true` and paper accounts only.
- The sample includes max drawdown, max trades per day, market-hours checks, a kill switch, and trade journaling, but still needs broader production hardening.
- Test extensively before any live deployment.