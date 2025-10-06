"""
Zerodha Kite Connect API Integration
For live trading implementation of SMA crossover strategy
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

class KiteConnectTrader:
    """
    Wrapper for Kite Connect API to implement live trading
    
    Note: This requires kiteconnect package and valid API credentials
    Install: pip install kiteconnect
    """
    
    def __init__(self, api_key, access_token):
        """
        Initialize Kite Connect client
        
        Args:
            api_key: Your Kite Connect API key
            access_token: Valid access token
        """
        try:
            from kiteconnect import KiteConnect, KiteTicker
            self.kite = KiteConnect(api_key=api_key)
            self.kite.set_access_token(access_token)
            self.api_key = api_key
            self.access_token = access_token
            print("Kite Connect initialized successfully")
        except ImportError:
            print("WARNING: kiteconnect package not installed")
            print("Install with: pip install kiteconnect")
            self.kite = None
        except Exception as e:
            print(f"Error initializing Kite Connect: {e}")
            self.kite = None
    
    def get_instruments(self):
        """
        Get list of all tradeable instruments
        
        Returns:
            DataFrame: Instrument data
        """
        if not self.kite:
            return None
        
        try:
            instruments = self.kite.instruments("NSE")
            df = pd.DataFrame(instruments)
            return df
        except Exception as e:
            print(f"Error fetching instruments: {e}")
            return None
    
    def get_instrument_token(self, symbol):
        """
        Get instrument token for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'NIFTYBEES', 'DIXON')
            
        Returns:
            int: Instrument token
        """
        instruments = self.get_instruments()
        if instruments is None:
            return None
        
        # Remove .NS suffix if present
        symbol = symbol.replace('.NS', '')
        
        instrument = instruments[instruments['tradingsymbol'] == symbol]
        if len(instrument) > 0:
            return instrument.iloc[0]['instrument_token']
        return None
    
    def get_historical_data(self, instrument_token, from_date, to_date, interval='5minute'):
        """
        Fetch historical intraday data
        
        Args:
            instrument_token: Instrument token
            from_date: Start date
            to_date: End date
            interval: Data interval ('minute', '5minute', '15minute', etc.)
            
        Returns:
            DataFrame: OHLCV data
        """
        if not self.kite:
            return None
        
        try:
            data = self.kite.historical_data(
                instrument_token,
                from_date,
                to_date,
                interval=interval
            )
            
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'date': 'Date',
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume'
            })
            df = df.set_index('Date')
            
            return df
        
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None
    
    def place_order(self, symbol, quantity, transaction_type, order_type='MARKET',
                   product='MIS', price=None, trigger_price=None, stop_loss=None, 
                   take_profit=None):
        """
        Place an order
        
        Args:
            symbol: Trading symbol
            quantity: Number of shares
            transaction_type: 'BUY' or 'SELL'
            order_type: 'MARKET', 'LIMIT', 'SL', 'SL-M'
            product: 'CNC' (delivery) or 'MIS' (intraday)
            price: Limit price (for LIMIT orders)
            trigger_price: Trigger price (for SL orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            str: Order ID
        """
        if not self.kite:
            print("Kite Connect not initialized")
            return None
        
        try:
            # Remove .NS suffix
            symbol = symbol.replace('.NS', '')
            
            order_params = {
                'tradingsymbol': symbol,
                'exchange': 'NSE',
                'transaction_type': transaction_type,
                'quantity': quantity,
                'order_type': order_type,
                'product': product,
                'validity': 'DAY'
            }
            
            if price:
                order_params['price'] = price
            
            if trigger_price:
                order_params['trigger_price'] = trigger_price
            
            order_id = self.kite.place_order(**order_params)
            print(f"Order placed successfully. Order ID: {order_id}")
            
            # Place stop-loss and take-profit as separate orders if needed
            if stop_loss and order_id:
                self._place_exit_order(symbol, quantity, 'SL', stop_loss, product)
            
            if take_profit and order_id:
                self._place_exit_order(symbol, quantity, 'LIMIT', take_profit, product)
            
            return order_id
        
        except Exception as e:
            print(f"Error placing order: {e}")
            return None
    
    def _place_exit_order(self, symbol, quantity, order_type, price, product):
        """Place exit order (stop-loss or take-profit)"""
        try:
            # Determine transaction type (opposite of entry)
            # This is a simplified version - in practice, check current position
            exit_params = {
                'tradingsymbol': symbol,
                'exchange': 'NSE',
                'transaction_type': 'SELL',  # Assume we're exiting a long position
                'quantity': quantity,
                'order_type': order_type,
                'product': product,
                'price': price,
                'validity': 'DAY'
            }
            
            if order_type == 'SL':
                exit_params['trigger_price'] = price
            
            order_id = self.kite.place_order(**exit_params)
            print(f"Exit order placed. Order ID: {order_id}")
            return order_id
        
        except Exception as e:
            print(f"Error placing exit order: {e}")
            return None
    
    def get_positions(self):
        """
        Get current positions
        
        Returns:
            dict: Current positions
        """
        if not self.kite:
            return None
        
        try:
            positions = self.kite.positions()
            return positions
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return None
    
    def get_orders(self):
        """
        Get all orders for the day
        
        Returns:
            list: List of orders
        """
        if not self.kite:
            return None
        
        try:
            orders = self.kite.orders()
            return orders
        except Exception as e:
            print(f"Error fetching orders: {e}")
            return None
    
    def cancel_order(self, order_id, variety='regular'):
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
            variety: Order variety
            
        Returns:
            bool: Success status
        """
        if not self.kite:
            return False
        
        try:
            self.kite.cancel_order(variety=variety, order_id=order_id)
            print(f"Order {order_id} cancelled successfully")
            return True
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False
    
    def get_quote(self, symbol):
        """
        Get real-time quote
        
        Args:
            symbol: Trading symbol
            
        Returns:
            dict: Quote data
        """
        if not self.kite:
            return None
        
        try:
            symbol = symbol.replace('.NS', '')
            quote = self.kite.quote([f"NSE:{symbol}"])
            return quote
        except Exception as e:
            print(f"Error fetching quote: {e}")
            return None


class LiveSMAStrategy:
    """
    Live implementation of SMA crossover strategy
    """
    
    def __init__(self, kite_trader, symbol, short_sma, long_sma, 
                 stop_loss=0.05, take_profit=0.10, trade_mode='MIS',
                 position_size=0.01, interval='5minute'):
        """
        Initialize live strategy
        
        Args:
            kite_trader: KiteConnectTrader instance
            symbol: Trading symbol
            short_sma: Short SMA period
            long_sma: Long SMA period
            stop_loss: Stop loss percentage
            take_profit: Take profit percentage
            trade_mode: 'CNC' or 'MIS'
            position_size: Position size as fraction of capital
            interval: Data interval
        """
        self.kite = kite_trader
        self.symbol = symbol
        self.short_sma = short_sma
        self.long_sma = long_sma
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trade_mode = trade_mode
        self.position_size = position_size
        self.interval = interval
        
        # Get instrument token
        self.instrument_token = self.kite.get_instrument_token(symbol)
        
        # Initialize data buffer
        self.data_buffer = pd.DataFrame()
        
        print(f"Live strategy initialized for {symbol}")
        print(f"  Short SMA: {short_sma}, Long SMA: {long_sma}")
        print(f"  Stop Loss: {stop_loss:.1%}, Take Profit: {take_profit:.1%}")
        print(f"  Trade Mode: {trade_mode}")
    
    def update_data(self):
        """Fetch latest data and update buffer"""
        if not self.instrument_token:
            return False
        
        # Fetch last N days of data
        to_date = datetime.now()
        from_date = to_date - timedelta(days=30)
        
        data = self.kite.get_historical_data(
            self.instrument_token,
            from_date,
            to_date,
            interval=self.interval
        )
        
        if data is not None and len(data) > 0:
            self.data_buffer = data
            return True
        
        return False
    
    def calculate_signals(self):
        """Calculate SMA and generate signals"""
        if len(self.data_buffer) < self.long_sma:
            print("Insufficient data for SMA calculation")
            return None
        
        # Calculate SMAs
        self.data_buffer['SMA_Short'] = self.data_buffer['Close'].rolling(self.short_sma).mean()
        self.data_buffer['SMA_Long'] = self.data_buffer['Close'].rolling(self.long_sma).mean()
        
        # Check for crossover
        if len(self.data_buffer) < 2:
            return None
        
        prev_short = self.data_buffer['SMA_Short'].iloc[-2]
        prev_long = self.data_buffer['SMA_Long'].iloc[-2]
        curr_short = self.data_buffer['SMA_Short'].iloc[-1]
        curr_long = self.data_buffer['SMA_Long'].iloc[-1]
        
        # Bullish crossover
        if prev_short <= prev_long and curr_short > curr_long:
            return 'BUY'
        
        # Bearish crossover (for shorting if allowed)
        if prev_short >= prev_long and curr_short < curr_long:
            return 'SELL'
        
        return None
    
    def execute_signal(self, signal):
        """Execute trading signal"""
        if signal is None:
            return
        
        # Get current quote
        quote = self.kite.get_quote(self.symbol)
        if not quote:
            print("Failed to get quote")
            return
        
        symbol_key = f"NSE:{self.symbol.replace('.NS', '')}"
        current_price = quote[symbol_key]['last_price']
        
        # Calculate position size
        # This is simplified - in practice, get actual account balance
        account_capital = 100000  # Placeholder
        position_value = account_capital * self.position_size
        quantity = int(position_value / current_price)
        
        if quantity < 1:
            print("Quantity too small to trade")
            return
        
        # Calculate stop-loss and take-profit prices
        if signal == 'BUY':
            sl_price = current_price * (1 - self.stop_loss)
            tp_price = current_price * (1 + self.take_profit)
            
            print(f"\nExecuting BUY signal:")
            print(f"  Symbol: {self.symbol}")
            print(f"  Quantity: {quantity}")
            print(f"  Price: ₹{current_price:.2f}")
            print(f"  Stop Loss: ₹{sl_price:.2f}")
            print(f"  Take Profit: ₹{tp_price:.2f}")
            
            # Place order
            order_id = self.kite.place_order(
                symbol=self.symbol,
                quantity=quantity,
                transaction_type='BUY',
                order_type='MARKET',
                product=self.trade_mode,
                stop_loss=sl_price,
                take_profit=tp_price
            )
            
            if order_id:
                print(f"Order executed successfully. Order ID: {order_id}")
        
        elif signal == 'SELL':
            # Only execute if not in delivery mode
            if self.trade_mode == 'MIS':
                sl_price = current_price * (1 + self.stop_loss)
                tp_price = current_price * (1 - self.take_profit)
                
                print(f"\nExecuting SELL signal:")
                print(f"  Symbol: {self.symbol}")
                print(f"  Quantity: {quantity}")
                print(f"  Price: ₹{current_price:.2f}")
                
                order_id = self.kite.place_order(
                    symbol=self.symbol,
                    quantity=quantity,
                    transaction_type='SELL',
                    order_type='MARKET',
                    product=self.trade_mode
                )
                
                if order_id:
                    print(f"Order executed successfully. Order ID: {order_id}")
    
    def run(self, check_interval=300):
        """
        Run strategy in live mode
        
        Args:
            check_interval: Seconds between checks (default 300 = 5 minutes)
        """
        print(f"\nStarting live strategy for {self.symbol}")
        print(f"Checking every {check_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Check if market is open (9:15 AM - 3:30 PM IST)
                now = datetime.now()
                market_open = now.replace(hour=9, minute=15, second=0)
                market_close = now.replace(hour=15, minute=30, second=0)
                
                if market_open <= now <= market_close:
                    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Checking for signals...")
                    
                    # Update data
                    if self.update_data():
                        # Calculate signals
                        signal = self.calculate_signals()
                        
                        if signal:
                            print(f"Signal detected: {signal}")
                            self.execute_signal(signal)
                        else:
                            print("No signal")
                else:
                    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Market closed")
                
                # Wait for next check
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            print("\nStrategy stopped by user")


def setup_guide():
    """Print setup guide for Kite Connect"""
    print("\n" + "=" * 80)
    print("ZERODHA KITE CONNECT SETUP GUIDE")
    print("=" * 80)
    print("""
1. Create Kite Connect App:
   - Go to https://developers.kite.trade/
   - Login with your Zerodha credentials
   - Click on "Create New App"
   - Fill in app details (name, redirect URL, etc.)
   - Note your API Key and API Secret

2. Install kiteconnect package:
   pip install kiteconnect

3. Generate Access Token:
   - Use the login flow to get request token
   - Exchange request token for access token
   - Access tokens expire daily (need to regenerate)

4. Example Usage:
   
   from kite_integration import KiteConnectTrader, LiveSMAStrategy
   
   # Initialize trader
   api_key = "your_api_key"
   access_token = "your_access_token"
   trader = KiteConnectTrader(api_key, access_token)
   
   # Create live strategy
   strategy = LiveSMAStrategy(
       kite_trader=trader,
       symbol='NIFTYBEES.NS',
       short_sma=10,
       long_sma=50,
       stop_loss=0.05,
       take_profit=0.10,
       trade_mode='MIS'
   )
   
   # Run strategy (checks every 5 minutes)
   strategy.run(check_interval=300)

5. Important Notes:
   - Kite Connect has rate limits (3 requests/second)
   - Access tokens expire daily at 7:30 AM
   - Test with small quantities first
   - Always use stop-losses
   - MIS positions auto-squareoff at 3:20 PM
   - Maintain sufficient margin for MIS trades

6. Security:
   - Never share API keys or tokens
   - Use environment variables for credentials
   - Enable 2FA on your Zerodha account
   - Regularly review API access logs

For detailed documentation: https://kite.trade/docs/connect/v3/
    """)
    print("=" * 80)


if __name__ == "__main__":
    setup_guide()
