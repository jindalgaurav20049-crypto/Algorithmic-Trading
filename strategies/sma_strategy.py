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
import datetime as dt
import numpy as np

# --- 1. Download Nifty 50 data ---
print("--- Step 1: Downloading Nifty 50 historical data ---")
ticker_symbol = "^NSEI"
start_date, end_date = dt.datetime(2018, 1, 1), dt.datetime(2025, 1, 1)

data = yf.download(ticker_symbol, start=start_date, end=end_date, auto_adjust=True)
data.columns = [c.capitalize() if not isinstance(c, tuple) else c[0].capitalize() for c in data.columns]
data = data[["Open", "High", "Low", "Close", "Volume"]].dropna().reset_index(drop=True)
print(f"Data ready: {data.shape}")

# --- 2. Multi-timeframe SMA Trend Strategy with margin-safe sizing ---
class NiftyTrendOptimized(Strategy):
    short1 = 10
    long1  = 50
    short2 = 20
    long2  = 100
    stop_loss = 0.05
    trailing = True
    risk_per_trade = 0.02  # Fraction of free equity to risk per trade

    def init(self):
        close = self.data.Close
        self.sma1_short = self.I(lambda x: pd.Series(x).rolling(self.short1).mean(), close)
        self.sma1_long  = self.I(lambda x: pd.Series(x).rolling(self.long1).mean(), close)
        self.sma2_short = self.I(lambda x: pd.Series(x).rolling(self.short2).mean(), close)
        self.sma2_long  = self.I(lambda x: pd.Series(x).rolling(self.long2).mean(), close)

    def next(self):
        price = self.data.Close[-1]

        # --- Manage stop-loss / trailing ---
        for trade in self.trades:
            if trade.is_long:
                if self.trailing:
                    trade.sl = max(trade.sl, price * (1 - self.stop_loss)) if trade.sl else price * (1 - self.stop_loss)
                elif price < trade.entry_price * (1 - self.stop_loss):
                    trade.close()
            elif trade.is_short:
                if self.trailing:
                    trade.sl = min(trade.sl, price * (1 + self.stop_loss)) if trade.sl else price * (1 + self.stop_loss)
                elif price > trade.entry_price * (1 + self.stop_loss):
                    trade.close()

        # --- Trend filter signals ---
        long_signal  = self.sma1_short[-1] > self.sma1_long[-1] and self.sma2_short[-1] > self.sma2_long[-1]
        short_signal = self.sma1_short[-1] < self.sma1_long[-1] and self.sma2_short[-1] < self.sma2_long[-1]

        # --- Margin-safe position sizing ---
        free_equity = self.equity
        if self.position:
            free_equity -= abs(self.position.size * price)

        max_affordable = int(free_equity // price)  # maximum units possible
        size = int((free_equity * self.risk_per_trade) // price)
        size = min(size, max_affordable)

        if size < 1:  # skip if too small
            return

        # --- Entry logic ---
        if long_signal:
            if self.position and self.position.is_short:
                self.position.close()
            if not self.position:
                self.buy(size=size, sl=price*(1-self.stop_loss) if not self.trailing else None)

        elif short_signal:
            if self.position and self.position.is_long:
                self.position.close()
            if not self.position:
                self.sell(size=size, sl=price*(1+self.stop_loss) if not self.trailing else None)

    def finalize(self):
        if self.position:
            self.position.close()

# --- 3. Baseline backtest ---
bt = Backtest(data, NiftyTrendOptimized, cash=100000, commission=0.001)
stats = bt.run()
print(stats)
bt.plot(filename="nifty_trend_initial", open_browser=False)

# --- 4. Manual grid search optimization ---
short1_range = range(5, 21, 5)
long1_range  = range(30, 101, 10)
short2_range = range(10, 31, 5)
long2_range  = range(50, 151, 10)
sl_values    = [0.03, 0.05, 0.07]

best_params = None
best_equity = -np.inf

for s1 in short1_range:
    for l1 in long1_range:
        if s1 >= l1: continue
        for s2 in short2_range:
            for l2 in long2_range:
                if s2 >= l2: continue
                for sl in sl_values:
                    NiftyTrendOptimized.short1 = s1
                    NiftyTrendOptimized.long1  = l1
                    NiftyTrendOptimized.short2 = s2
                    NiftyTrendOptimized.long2  = l2
                    NiftyTrendOptimized.stop_loss = sl

                    stats = bt.run()
                    equity = stats["Equity Final [$]"]

                    print(f"Tested s1={s1},l1={l1},s2={s2},l2={l2},sl={sl:.2%} → Equity={equity:.2f}")

                    if equity > best_equity:
                        best_equity = equity
                        best_params = (s1,l1,s2,l2,sl)

print("\nBest Parameters Found:", best_params, "with Final Equity:", best_equity)

# --- 5. Backtest with best parameters ---
NiftyTrendOptimized.short1, NiftyTrendOptimized.long1, \
NiftyTrendOptimized.short2, NiftyTrendOptimized.long2, \
NiftyTrendOptimized.stop_loss = best_params

bt_best = Backtest(data, NiftyTrendOptimized, cash=100000, commission=0.001)
stats_best = bt_best.run()
print("\n--- Final Optimized Stats ---")
print(stats_best)
bt_best.plot(filename="nifty_trend_optimized", open_browser=False)
