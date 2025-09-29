import yfinance as yf
from backtesting import Backtest, Strategy
import pandas as pd

def ATR(df, n=14):
    df['H-L'] = df['High'] - df['Low']
    df['H-C'] = abs(df['High'] - df['Close'].shift())
    df['L-C'] = abs(df['Low'] - df['Close'].shift())
    tr = df[['H-L','H-C','L-C']].max(axis=1)
    return tr.rolling(n).mean()

class ATROptimized(Strategy):
    atr_period = 14
    stop_loss = 0.05
    trailing = True
    risk_per_trade = 0.02

    def init(self):
        self.atr = self.I(ATR, self.data.df, self.atr_period)

    def next(self):
        price = self.data.Close[-1]

        # --- Manage stop-loss / trailing ---
        for trade in self.trades:
            if trade.is_long:
                if self.trailing:
                    trade.sl = max(trade.sl, price - 2 * self.atr[-1]) if trade.sl else price - 2 * self.atr[-1]
                elif price < trade.entry_price - 2 * self.atr[-1]:
                    trade.close()
            elif trade.is_short:
                if self.trailing:
                    trade.sl = min(trade.sl, price + 2 * self.atr[-1]) if trade.sl else price + 2 * self.atr[-1]
                elif price > trade.entry_price + 2 * self.atr[-1]:
                    trade.close()

        # --- Signal logic (trend following with ATR filter) ---
        long_signal = price > self.data.Close[-2] and self.data.Close[-1] > self.data.Open[-1]
        short_signal = price < self.data.Close[-2] and self.data.Close[-1] < self.data.Open[-1]

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
                self.buy(size=size, sl=price - 2*self.atr[-1] if not self.trailing else None)

        elif short_signal:
            if self.position and self.position.is_long:
                self.position.close()
            if not self.position:
                self.sell(size=size, sl=price + 2*self.atr[-1] if not self.trailing else None)

    def finalize(self):
        if self.position:
            self.position.close()

if __name__ == "__main__":
    data = yf.download("INFY.NS", start="2018-01-01", end="2025-01-01", auto_adjust=True)
    data = data[['Open','High','Low','Close','Volume']]
    bt = Backtest(data, ATROptimized, cash=100000, commission=0.001)
    stats = bt.run()
    print(stats)
    bt.plot(filename="atr_strategy", open_browser=False)
