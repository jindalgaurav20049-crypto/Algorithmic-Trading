"""
Live Trading Implementation - SMA Crossover Strategy
Auto-generated from optimization results

OPTIMAL PARAMETERS:
- Short SMA: 8 days
- Long SMA: 20 days
- Max Holding Period: 60 days
- Stop-Loss: 0.00%
- Take-Profit: 0.00%
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class LiveSMAStrategy:
    def __init__(self, account_size=100000, risk_per_trade=0.01):
        # Optimized parameters
        self.short_sma = 8
        self.long_sma = 20
        self.max_holding_period = 60
        self.stop_loss = 0.0
        self.take_profit = 0.0
        
        # Account parameters
        self.account_size = account_size
        self.risk_per_trade = risk_per_trade
        
        # Position tracking
        self.position = None
        self.entry_price = None
        self.entry_date = None
        
    def calculate_sma(self, prices, period):
        """Calculate Simple Moving Average"""
        return prices.rolling(window=period).mean()
    
    def calculate_position_size(self, price):
        """Calculate position size based on risk management"""
        # Risk amount per trade
        risk_amount = self.account_size * self.risk_per_trade
        
        # Position size based on stop-loss
        if self.stop_loss > 0:
            position_value = risk_amount / self.stop_loss
            shares = int(position_value / price)
        else:
            # If no stop-loss, use 10% of account
            shares = int((self.account_size * 0.1) / price)
        
        return max(1, shares)
    
    def check_entry_signal(self, data):
        """Check for entry signals"""
        if len(data) < self.long_sma:
            return False, None
        
        short_ma = self.calculate_sma(data['Close'], self.short_sma)
        long_ma = self.calculate_sma(data['Close'], self.long_sma)
        
        # Buy signal: short MA crosses above long MA
        if short_ma.iloc[-2] <= long_ma.iloc[-2] and short_ma.iloc[-1] > long_ma.iloc[-1]:
            return True, 'BUY'
        
        return False, None
    
    def check_exit_signal(self, data, current_price):
        """Check for exit signals"""
        if self.position is None:
            return False, None
        
        # Check stop-loss
        if current_price <= self.entry_price * (1 - self.stop_loss):
            return True, 'STOP_LOSS'
        
        # Check take-profit
        if current_price >= self.entry_price * (1 + self.take_profit):
            return True, 'TAKE_PROFIT'
        
        # Check maximum holding period
        days_held = (datetime.now() - self.entry_date).days
        if days_held >= self.max_holding_period:
            return True, 'MAX_HOLDING'
        
        # Check for crossover exit
        if len(data) >= self.long_sma:
            short_ma = self.calculate_sma(data['Close'], self.short_sma)
            long_ma = self.calculate_sma(data['Close'], self.long_sma)
            
            if short_ma.iloc[-2] >= long_ma.iloc[-2] and short_ma.iloc[-1] < long_ma.iloc[-1]:
                return True, 'CROSSOVER'
        
        return False, None
    
    def execute_trade(self, symbol, action, price, shares):
        """Execute trade via broker API"""
        print(f"{datetime.now()}: {action} {shares} shares of {symbol} at {price}")
        
        # Implement broker-specific API calls here
        # Examples for different brokers:
        
        # Zerodha (Kite Connect):
        # kite.place_order(tradingsymbol=symbol, exchange="NSE",
        #                  transaction_type=action, quantity=shares,
        #                  order_type="LIMIT", price=price, product="CNC")
        
        # Interactive Brokers:
        # order = LimitOrder(action, shares, price)
        # ib.placeOrder(contract, order)
        
        # Alpaca:
        # api.submit_order(symbol=symbol, qty=shares, side=action.lower(),
        #                  type='limit', limit_price=price, time_in_force='day')
        
        return True
    
    def run(self, data, current_price, symbol='NIFTY'):
        """Main strategy execution loop"""
        # Check for entry signals (if not in position)
        if self.position is None:
            has_signal, signal_type = self.check_entry_signal(data)
            
            if has_signal and signal_type == 'BUY':
                shares = self.calculate_position_size(current_price)
                
                if self.execute_trade(symbol, 'BUY', current_price, shares):
                    self.position = shares
                    self.entry_price = current_price
                    self.entry_date = datetime.now()
                    print(f"ENTERED POSITION: {shares} shares at {current_price}")
        
        # Check for exit signals (if in position)
        else:
            should_exit, exit_reason = self.check_exit_signal(data, current_price)
            
            if should_exit:
                if self.execute_trade(symbol, 'SELL', current_price, self.position):
                    pnl = (current_price - self.entry_price) * self.position
                    pnl_pct = (current_price / self.entry_price - 1) * 100
                    
                    print(f"EXITED POSITION: {self.position} shares at {current_price}")
                    print(f"Reason: {exit_reason}")
                    print(f"P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
                    
                    self.position = None
                    self.entry_price = None
                    self.entry_date = None

# Example usage:
if __name__ == "__main__":
    # Initialize strategy
    strategy = LiveSMAStrategy(account_size=100000, risk_per_trade=0.01)
    
    # Load historical data (replace with real-time data feed)
    # data = get_historical_data('NIFTY', days=365)
    # current_price = get_current_price('NIFTY')
    
    # Run strategy
    # strategy.run(data, current_price, symbol='NIFTY')
    
    print("Strategy initialized with optimized parameters")
    print(f"Short SMA: {strategy.short_sma}")
    print(f"Long SMA: {strategy.long_sma}")
    print(f"Max Holding: {strategy.max_holding_period} days")
    print(f"Stop-Loss: {strategy.stop_loss:.2%}")
    print(f"Take-Profit: {strategy.take_profit:.2%}")
