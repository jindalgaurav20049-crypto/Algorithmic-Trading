"""
Advanced SMA Crossover Strategy with Zerodha Integration
Supports both CNC (Delivery) and MIS (Intraday) modes with realistic transaction costs
"""

from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np
from datetime import time

class AdvancedSMACrossover(Strategy):
    """
    SMA Crossover strategy with extensive parameterization
    
    Parameters:
        short_sma: Short-term SMA period
        long_sma: Long-term SMA period
        stop_loss: Stop-loss percentage (0-1)
        take_profit: Take-profit percentage (0-1)
        trade_mode: 'CNC' or 'MIS'
        entry_window: Minutes to wait after signal (0-30)
        position_size: Risk per trade as fraction of equity (0.005-0.02)
        squareoff_time: Time to auto-squareoff MIS positions (default 15:20)
    """
    
    # Default parameters
    short_sma = 10
    long_sma = 50
    stop_loss = 0.05  # 5%
    take_profit = 0.10  # 10%
    trade_mode = 'MIS'
    entry_window = 0  # minutes
    position_size = 0.01  # 1% risk
    long_only = True  # For delivery trades
    
    def init(self):
        """Initialize strategy indicators"""
        close = self.data.Close
        
        # Calculate SMAs
        self.sma_short = self.I(lambda x: pd.Series(x).rolling(self.short_sma).mean(), close)
        self.sma_long = self.I(lambda x: pd.Series(x).rolling(self.long_sma).mean(), close)
        
        # Track signals
        self.signal_bar = None
        self.signal_type = None
        
    def next(self):
        """Execute strategy logic on each bar"""
        price = self.data.Close[-1]
        current_time = self.data.index[-1]
        
        # Auto-squareoff for MIS positions (3:20 PM)
        if self.trade_mode == 'MIS':
            if hasattr(current_time, 'hour'):
                if current_time.hour == 15 and current_time.minute >= 20:
                    if self.position:
                        self.position.close()
                    return
        
        # Manage existing positions
        if self.position:
            entry_price = self.position.entry_price if hasattr(self.position, 'entry_price') else price
            
            # Stop-loss check
            if self.position.is_long:
                if self.stop_loss > 0 and price <= entry_price * (1 - self.stop_loss):
                    self.position.close()
                    return
                # Take-profit check
                if self.take_profit > 0 and price >= entry_price * (1 + self.take_profit):
                    self.position.close()
                    return
            elif self.position.is_short:
                if self.stop_loss > 0 and price >= entry_price * (1 + self.stop_loss):
                    self.position.close()
                    return
                if self.take_profit > 0 and price <= entry_price * (1 - self.take_profit):
                    self.position.close()
                    return
        
        # Generate signals
        if len(self.sma_short) < 2 or len(self.sma_long) < 2:
            return
        
        # Crossover detection
        prev_short = self.sma_short[-2]
        prev_long = self.sma_long[-2]
        curr_short = self.sma_short[-1]
        curr_long = self.sma_long[-1]
        
        # Bullish crossover
        if prev_short <= prev_long and curr_short > curr_long:
            self.signal_bar = len(self.data) - 1
            self.signal_type = 'long'
        
        # Bearish crossover
        if prev_short >= prev_long and curr_short < curr_long:
            self.signal_bar = len(self.data) - 1
            self.signal_type = 'short'
        
        # Execute entry after entry_window
        if self.signal_bar is not None:
            bars_since_signal = len(self.data) - 1 - self.signal_bar
            
            # Check if within entry window
            if bars_since_signal > 0 and bars_since_signal <= (self.entry_window // 5):  # Assuming 5-min bars
                if self.signal_type == 'long' and not self.position:
                    size = self._calculate_position_size(price)
                    if size > 0:
                        self.buy(size=size)
                        self.signal_bar = None
                        self.signal_type = None
                
                elif self.signal_type == 'short' and not self.long_only and not self.position:
                    size = self._calculate_position_size(price)
                    if size > 0:
                        self.sell(size=size)
                        self.signal_bar = None
                        self.signal_type = None
            
            # Clear old signals
            if bars_since_signal > (self.entry_window // 5):
                self.signal_bar = None
                self.signal_type = None
    
    def _calculate_position_size(self, price):
        """
        Calculate position size based on risk parameters
        
        Args:
            price: Current price
            
        Returns:
            int: Number of shares to trade
        """
        # Available equity
        available_equity = self.equity
        
        # Risk amount
        risk_amount = available_equity * self.position_size
        
        # Position size based on stop-loss
        if self.stop_loss > 0:
            size = int(risk_amount / (price * self.stop_loss))
        else:
            # If no stop-loss, use position_size directly
            size = int((available_equity * self.position_size) / price)
        
        # Ensure we don't exceed available equity
        max_size = int(available_equity / price)
        size = min(size, max_size)
        
        return max(size, 0)


class BuyAndHoldStrategy(Strategy):
    """Simple buy-and-hold strategy for comparison"""
    
    def init(self):
        pass
    
    def next(self):
        if not self.position:
            # Buy with all available capital
            size = int(self.equity / self.data.Close[-1])
            if size > 0:
                self.buy(size=size)
