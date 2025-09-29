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

# --- 2. MACD Strategy ---
class MacdStrategy(Strategy):
    short = 12
    long = 26
    signal = 9
    stop_loss = 0.05
    risk_per_trade = 0.02

    def init(self):
        close = self.data.Close
        exp1 = pd.Series(close).ewm(span=self.short, adjust=False).mean()
        exp2 = pd.Series(close).ewm(span=self.long, adjust=False).mean()
        self.macd = exp1 - exp2
        self.signal_line = self.macd.ewm(span=self.signal, adjust=False).mean()
        self.macd = self.I(lambda x: pd.Series(x).ewm(span=self.short, adjust=False).mean() -
                                 pd.Series(x).ewm(span=self.long, adjust=False).mean(), close)
        self.signal_line = self.I(lambda x: pd.Series(x).ewm(span=self.signal, adjust=False).mean(), self.macd)

    def next(self):
        price = self.data.Close[-1]

        # stop-loss check
        for trade in self.trades:
            if trade.is_long and price < trade.entry_price * (1 - self.stop_loss):
                trade.close()
            elif trade.is_short and price > trade.entry_price * (1 + self.stop_loss):
                trade.close()

        long_signal  = self.macd[-1] > self.signal_line[-1]
        short_signal = self.macd[-1] < self.signal_line[-1]

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
bt = Backtest(data, MacdStrategy, cash=100000, commission=0.001)
stats = bt.run()
print(stats)
bt.plot(filename="macd_strategy_initial", open_browser=False)

# --- 4. Manual optimization ---
short_range = [8, 12, 16]
long_range  = [20, 26, 32]
signal_range= [7, 9, 11]
sl_values   = [0.03, 0.05, 0.07]

best_params, best_equity = None, -np.inf
for s in short_range:
    for l in long_range:
        if s >= l: continue
        for sig in signal_range:
            for sl in sl_values:
                MacdStrategy.short, MacdStrategy.long, MacdStrategy.signal, MacdStrategy.stop_loss = s, l, sig, sl
                stats = bt.run()
                equity = stats["Equity Final [$]"]
                print(f"Tested short={s}, long={l}, sig={sig}, sl={sl:.2%} → Equity={equity:.2f}")
                if equity > best_equity:
                    best_equity = equity
                    best_params = (s, l, sig, sl)

print("\nBest Params:", best_params, "→ Equity:", best_equity)

# --- 5. Run with best params ---
MacdStrategy.short, MacdStrategy.long, MacdStrategy.signal, MacdStrategy.stop_loss = best_params
bt_best = Backtest(data, MacdStrategy, cash=100000, commission=0.001)
stats_best = bt_best.run()
print("\n--- Final Optimized Stats ---")
print(stats_best)
bt_best.plot(filename="macd_strategy_optimized", open_browser=False)
