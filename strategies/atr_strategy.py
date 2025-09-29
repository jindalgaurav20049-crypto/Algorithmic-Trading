# --- 0. Install required packages ---
import subprocess, sys
def install_package(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
for pkg in ["backtesting", "yfinance", "pandas", "matplotlib", "bokeh", "numpy"]:
    install_package(pkg)

# --- Imports ---
from backtesting import Backtest, Strategy
import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt

# --- 1. Download Nifty 50 data ---
print("--- Step 1: Downloading Nifty 50 historical data ---")
ticker_symbol = "^NSEI"
start_date, end_date = dt.datetime(2018, 1, 1), dt.datetime(2025, 1, 1)

data = yf.download(ticker_symbol, start=start_date, end=end_date, auto_adjust=True)
data.columns = [c.capitalize() if not isinstance(c, tuple) else c[0].capitalize() for c in data.columns]
data = data[["Open", "High", "Low", "Close", "Volume"]].dropna().reset_index(drop=True)
print(f"Data ready: {data.shape}")

# --- 2. ATR Breakout Strategy ---
class AtrBreakout(Strategy):
    atr_period = 14
    atr_mult   = 1.5
    stop_loss  = 0.05
    risk_per_trade = 0.02

    def init(self):
        high, low, close = self.data.High, self.data.Low, self.data.Close
        tr = pd.concat([
            high - low,
            abs(high - close.shift(1)),
            abs(low - close.shift(1))
        ], axis=1).max(axis=1)

        atr = tr.rolling(self.atr_period).mean()
        self.atr = self.I(lambda x: atr, close)

    def next(self):
        price = self.data.Close[-1]
        atr_val = self.atr[-1]
        prev_high = self.data.High[-2]
        prev_low  = self.data.Low[-2]

        # stop-loss handling
        for trade in self.trades:
            if trade.is_long and price < trade.entry_price * (1 - self.stop_loss):
                trade.close()
            elif trade.is_short and price > trade.entry_price * (1 + self.stop_loss):
                trade.close()

        # signals
        long_signal  = price > prev_high + self.atr_mult * atr_val
        short_signal = price < prev_low  - self.atr_mult * atr_val

        # position sizing
        free_equity = self.equity
        if self.position:
            free_equity -= abs(self.position.size * price)
        size = int((free_equity * self.risk_per_trade) // price)

        if size < 1: return

        if long_signal:
            if self.position and self.position.is_short:
                self.position.close()
            if not self.position:
                self.buy(size=size, sl=price*(1-self.stop_loss))

        elif short_signal:
            if self.position and self.position.is_long:
                self.position.close()
            if not self.position:
                self.sell(size=size, sl=price*(1+self.stop_loss))

    def finalize(self):
        if self.position:
            self.position.close()

# --- 3. Baseline backtest ---
bt = Backtest(data, AtrBreakout, cash=100000, commission=0.001)
stats = bt.run()
print(stats)
bt.plot(filename="atr_breakout_initial", open_browser=False)

# --- 4. Manual optimization ---
atr_periods = [10, 14, 20]
atr_multipliers = [1.0, 1.5, 2.0]
sl_values   = [0.03, 0.05, 0.07]

best_params, best_equity = None, -np.inf
for p in atr_periods:
    for m in atr_multipliers:
        for sl in sl_values:
            AtrBreakout.atr_period = p
            AtrBreakout.atr_mult   = m
            AtrBreakout.stop_loss  = sl

            stats = bt.run()
            equity = stats["Equity Final [$]"]

            print(f"Tested period={p}, mult={m}, sl={sl:.2%} → Equity={equity:.2f}")
            if equity > best_equity:
                best_equity = equity
                best_params = (p, m, sl)

print("\nBest Params:", best_params, "→ Equity:", best_equity)

# --- 5. Run with best params ---
AtrBreakout.atr_period, AtrBreakout.atr_mult, AtrBreakout.stop_loss = best_params
bt_best = Backtest(data, AtrBreakout, cash=100000, commission=0.001)
stats_best = bt_best.run()
print("\n--- Final Optimized Stats ---")
print(stats_best)
bt_best.plot(filename="atr_breakout_optimized", open_browser=False)
