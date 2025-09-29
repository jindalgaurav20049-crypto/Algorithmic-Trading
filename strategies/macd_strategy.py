import yfinance as yf
from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np

class MACDOptimized(Strategy):
    fast = 12
    slow = 26
    signal = 9
    stop_loss = 0.05
    trailing = True
    risk_per_trade = 0.02

    def init(self):
        close = self.data.Close
        ema_fast = self.I(lambda x: pd.Series(x).ewm(span=self.fast).mean(), close)
        ema_slow = self.I(lambda x: pd.Series(x).ewm(span=self.slow).mean(), close)
        self.macd_line = ema_fast - ema_slow
        self.signal_line = self.I(lambda x: pd.Series(x).ewm(span=self.signal).mean(), self.macd_line)

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

        # --- Signal logic ---
        long_signal = self.macd_line[-1] > self.signal_line[-1] and self.macd_line[-2] <= self.signal_line[-2]
        short_signal = self.macd_line[-1] < self.signal_line[-1] and self.macd_line[-2] >= self.signal_line[-2]

        # --- Position sizing ---
        free_equity = self.equity
        if self.position:
            free_equity -= abs(self.position.size * price)

        max_affordable = int(free_equity // price)
        size = int((free_equity * self.risk_per_trade) // price)
        size = min(size, max_affordable)
        if size < 1:
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

if __name__ == "__main__":
    data = yf.download("TCS.NS", start="2018-01-01", end="2025-01-01", auto_adjust=True)
    data = data[['Open','High','Low','Close','Volume']]
    bt = Backtest(data, MACDOptimized, cash=100000, commission=0.001)
    stats = bt.run()
    print(stats)
    bt.plot(filename="macd_strategy", open_browser=False)
