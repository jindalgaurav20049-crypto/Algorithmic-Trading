"""
Zerodha Kite Connect Integration for Index Rebalancing Strategy
================================================================

This module provides integration with Zerodha's Kite Connect API for live trading
of the Index Front-Running Rebalancing strategy.

Features:
- Authentication and session management
- Order placement (CNC and MIS)
- Position monitoring
- Stop-loss management
- Real-time P&L tracking

Author: Advanced Quantitative Trading System
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from kiteconnect import KiteConnect
    KITE_AVAILABLE = True
except ImportError:
    logger.warning("kiteconnect not installed. Run: pip install kiteconnect")
    KITE_AVAILABLE = False

# =====================================================
# SECTION 1: AUTHENTICATION & SESSION MANAGEMENT
# =====================================================

class ZerodhaAuth:
    """Handle Zerodha Kite Connect authentication"""
    
    def __init__(self, api_key: str, api_secret: str, access_token: Optional[str] = None):
        """
        Initialize Zerodha authentication
        
        Args:
            api_key: Kite Connect API key
            api_secret: Kite Connect API secret
            access_token: Pre-existing access token (optional)
        """
        if not KITE_AVAILABLE:
            raise ImportError("kiteconnect package is required. Install with: pip install kiteconnect")
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.kite = KiteConnect(api_key=api_key)
        
        if access_token:
            self.kite.set_access_token(access_token)
            self.access_token = access_token
        else:
            self.access_token = None
    
    def get_login_url(self) -> str:
        """
        Get login URL for manual authentication
        
        Returns:
            Login URL string
        """
        return self.kite.login_url()
    
    def authenticate(self, request_token: str) -> str:
        """
        Generate access token from request token
        
        Args:
            request_token: Request token from login redirect
        
        Returns:
            Access token string
        """
        data = self.kite.generate_session(request_token, api_secret=self.api_secret)
        self.access_token = data["access_token"]
        self.kite.set_access_token(self.access_token)
        
        logger.info("Authentication successful")
        return self.access_token
    
    def save_token(self, filepath: str = "zerodha_token.json"):
        """
        Save access token to file
        
        Args:
            filepath: Path to save token
        """
        if not self.access_token:
            raise ValueError("No access token to save")
        
        with open(filepath, 'w') as f:
            json.dump({
                'access_token': self.access_token,
                'timestamp': datetime.now().isoformat()
            }, f)
        
        logger.info(f"Token saved to {filepath}")
    
    def load_token(self, filepath: str = "zerodha_token.json") -> bool:
        """
        Load access token from file
        
        Args:
            filepath: Path to token file
        
        Returns:
            True if token loaded successfully
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.access_token = data['access_token']
            self.kite.set_access_token(self.access_token)
            
            logger.info(f"Token loaded from {filepath}")
            return True
        except FileNotFoundError:
            logger.warning(f"Token file {filepath} not found")
            return False
        except Exception as e:
            logger.error(f"Error loading token: {e}")
            return False

# =====================================================
# SECTION 2: ORDER MANAGEMENT
# =====================================================

class ZerodhaOrderManager:
    """Manage order placement and execution"""
    
    def __init__(self, kite: KiteConnect):
        """
        Initialize order manager
        
        Args:
            kite: Authenticated KiteConnect instance
        """
        self.kite = kite
    
    def place_long_order(self, symbol: str, quantity: int, price: float,
                         product: str = 'CNC', order_type: str = 'LIMIT') -> Optional[str]:
        """
        Place a long (buy) order
        
        Args:
            symbol: Stock symbol (without .NS suffix)
            quantity: Number of shares
            price: Limit price (for LIMIT orders)
            product: 'CNC' for delivery, 'MIS' for intraday
            order_type: 'LIMIT' or 'MARKET'
        
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            order_params = {
                'variety': self.kite.VARIETY_REGULAR,
                'exchange': self.kite.EXCHANGE_NSE,
                'tradingsymbol': symbol,
                'transaction_type': self.kite.TRANSACTION_TYPE_BUY,
                'quantity': quantity,
                'product': self.kite.PRODUCT_CNC if product == 'CNC' else self.kite.PRODUCT_MIS,
                'order_type': self.kite.ORDER_TYPE_LIMIT if order_type == 'LIMIT' else self.kite.ORDER_TYPE_MARKET,
                'validity': self.kite.VALIDITY_DAY
            }
            
            if order_type == 'LIMIT':
                order_params['price'] = price
            
            order_id = self.kite.place_order(**order_params)
            logger.info(f"Long order placed: {symbol} x {quantity} @ {price} ({product})")
            return order_id
            
        except Exception as e:
            logger.error(f"Error placing long order for {symbol}: {e}")
            return None
    
    def place_short_order(self, symbol: str, quantity: int, price: float,
                          product: str = 'MIS', order_type: str = 'LIMIT') -> Optional[str]:
        """
        Place a short (sell) order
        
        Args:
            symbol: Stock symbol (without .NS suffix)
            quantity: Number of shares
            price: Limit price (for LIMIT orders)
            product: 'MIS' for intraday (recommended for shorts)
            order_type: 'LIMIT' or 'MARKET'
        
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            order_params = {
                'variety': self.kite.VARIETY_REGULAR,
                'exchange': self.kite.EXCHANGE_NSE,
                'tradingsymbol': symbol,
                'transaction_type': self.kite.TRANSACTION_TYPE_SELL,
                'quantity': quantity,
                'product': self.kite.PRODUCT_MIS,  # MIS recommended for shorts
                'order_type': self.kite.ORDER_TYPE_LIMIT if order_type == 'LIMIT' else self.kite.ORDER_TYPE_MARKET,
                'validity': self.kite.VALIDITY_DAY
            }
            
            if order_type == 'LIMIT':
                order_params['price'] = price
            
            order_id = self.kite.place_order(**order_params)
            logger.info(f"Short order placed: {symbol} x {quantity} @ {price} ({product})")
            return order_id
            
        except Exception as e:
            logger.error(f"Error placing short order for {symbol}: {e}")
            return None
    
    def place_stop_loss_order(self, symbol: str, quantity: int, trigger_price: float,
                              price: float, transaction_type: str, product: str = 'CNC') -> Optional[str]:
        """
        Place a stop-loss order
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            trigger_price: Stop-loss trigger price
            price: Order price (slightly away from trigger)
            transaction_type: 'BUY' or 'SELL'
            product: 'CNC' or 'MIS'
        
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=symbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY if transaction_type == 'BUY' 
                                 else self.kite.TRANSACTION_TYPE_SELL,
                quantity=quantity,
                product=self.kite.PRODUCT_CNC if product == 'CNC' else self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_SL,
                price=price,
                trigger_price=trigger_price,
                validity=self.kite.VALIDITY_DAY
            )
            
            logger.info(f"Stop-loss order placed: {symbol} x {quantity} @ trigger {trigger_price}")
            return order_id
            
        except Exception as e:
            logger.error(f"Error placing stop-loss order for {symbol}: {e}")
            return None
    
    def cancel_order(self, order_id: str, variety: str = 'regular') -> bool:
        """
        Cancel an existing order
        
        Args:
            order_id: Order ID to cancel
            variety: Order variety
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.kite.cancel_order(variety=variety, order_id=order_id)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """
        Get status of an order
        
        Args:
            order_id: Order ID
        
        Returns:
            Order details dictionary or None
        """
        try:
            orders = self.kite.orders()
            for order in orders:
                if order['order_id'] == order_id:
                    return order
            return None
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return None

# =====================================================
# SECTION 3: POSITION MONITORING
# =====================================================

class ZerodhaPositionMonitor:
    """Monitor and manage positions"""
    
    def __init__(self, kite: KiteConnect):
        """
        Initialize position monitor
        
        Args:
            kite: Authenticated KiteConnect instance
        """
        self.kite = kite
    
    def get_positions(self) -> Dict[str, List[Dict]]:
        """
        Get all current positions
        
        Returns:
            Dictionary with 'net' and 'day' position lists
        """
        try:
            positions = self.kite.positions()
            logger.info(f"Retrieved {len(positions['net'])} net positions")
            return positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {'net': [], 'day': []}
    
    def get_position_pnl(self, symbol: str) -> Optional[Tuple[float, float]]:
        """
        Get P&L for a specific position
        
        Args:
            symbol: Stock symbol
        
        Returns:
            Tuple of (unrealized_pnl, realized_pnl) or None
        """
        try:
            positions = self.get_positions()
            for pos in positions['net']:
                if pos['tradingsymbol'] == symbol:
                    return (pos['pnl'], pos['m2m'])
            return None
        except Exception as e:
            logger.error(f"Error getting position P&L for {symbol}: {e}")
            return None
    
    def get_holdings(self) -> List[Dict]:
        """
        Get all holdings (delivery positions)
        
        Returns:
            List of holding dictionaries
        """
        try:
            holdings = self.kite.holdings()
            logger.info(f"Retrieved {len(holdings)} holdings")
            return holdings
        except Exception as e:
            logger.error(f"Error getting holdings: {e}")
            return []
    
    def close_position(self, symbol: str, quantity: int, transaction_type: str,
                       product: str = 'CNC') -> Optional[str]:
        """
        Close an existing position
        
        Args:
            symbol: Stock symbol
            quantity: Quantity to close
            transaction_type: 'BUY' (to close short) or 'SELL' (to close long)
            product: 'CNC' or 'MIS'
        
        Returns:
            Order ID if successful, None otherwise
        """
        try:
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=symbol,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY if transaction_type == 'BUY'
                                 else self.kite.TRANSACTION_TYPE_SELL,
                quantity=quantity,
                product=self.kite.PRODUCT_CNC if product == 'CNC' else self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_MARKET,
                validity=self.kite.VALIDITY_DAY
            )
            
            logger.info(f"Position closed: {symbol} x {quantity} ({transaction_type})")
            return order_id
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return None

# =====================================================
# SECTION 4: MARKET DATA
# =====================================================

class ZerodhaMarketData:
    """Access market data and quotes"""
    
    def __init__(self, kite: KiteConnect):
        """
        Initialize market data handler
        
        Args:
            kite: Authenticated KiteConnect instance
        """
        self.kite = kite
    
    def get_quote(self, symbols: List[str]) -> Dict:
        """
        Get current quotes for symbols
        
        Args:
            symbols: List of symbols (e.g., ['NSE:DIXON', 'NSE:INFY'])
        
        Returns:
            Dictionary of quotes
        """
        try:
            quotes = self.kite.quote(symbols)
            return quotes
        except Exception as e:
            logger.error(f"Error getting quotes: {e}")
            return {}
    
    def get_ltp(self, symbols: List[str]) -> Dict:
        """
        Get last traded price for symbols
        
        Args:
            symbols: List of symbols (e.g., ['NSE:DIXON', 'NSE:INFY'])
        
        Returns:
            Dictionary with LTP values
        """
        try:
            ltp = self.kite.ltp(symbols)
            return ltp
        except Exception as e:
            logger.error(f"Error getting LTP: {e}")
            return {}
    
    def get_ohlc(self, symbols: List[str]) -> Dict:
        """
        Get OHLC data for symbols
        
        Args:
            symbols: List of symbols
        
        Returns:
            Dictionary with OHLC data
        """
        try:
            ohlc = self.kite.ohlc(symbols)
            return ohlc
        except Exception as e:
            logger.error(f"Error getting OHLC: {e}")
            return {}

# =====================================================
# SECTION 5: REBALANCE TRADING BOT
# =====================================================

class IndexRebalanceTradingBot:
    """
    Automated trading bot for Index Rebalancing strategy
    """
    
    def __init__(self, api_key: str, api_secret: str, access_token: Optional[str] = None,
                 strategy_params: Optional[Dict] = None):
        """
        Initialize trading bot
        
        Args:
            api_key: Zerodha API key
            api_secret: Zerodha API secret
            access_token: Pre-existing access token (optional)
            strategy_params: Strategy parameters from optimization
        """
        # Authentication
        self.auth = ZerodhaAuth(api_key, api_secret, access_token)
        
        # Managers
        self.order_manager = ZerodhaOrderManager(self.auth.kite)
        self.position_monitor = ZerodhaPositionMonitor(self.auth.kite)
        self.market_data = ZerodhaMarketData(self.auth.kite)
        
        # Strategy parameters (use defaults if not provided)
        self.params = strategy_params or {
            'entry_days_post_announcement': 2,
            'exit_days_post_effective': 3,
            'position_size_pct': 2.5,
            'stop_loss_pct': 5.0,
            'take_profit_pct': 10.0,
            'flow_filter_cr': 500,
            'trade_mode': 'CNC'
        }
        
        # Active trades
        self.active_trades = {}
        
        logger.info("IndexRebalanceTradingBot initialized")
    
    def execute_rebalance_trade(self, event: Dict, capital: float):
        """
        Execute trades for a rebalance event
        
        Args:
            event: Rebalance event dictionary with:
                   - announcement_date
                   - effective_date
                   - added_stocks
                   - removed_stocks
                   - estimated_aum_inr_cr
            capital: Available trading capital
        """
        announcement_date = event['announcement_date']
        effective_date = event['effective_date']
        added_stocks = event['added_stocks']
        removed_stocks = event['removed_stocks']
        estimated_flow = event['estimated_aum_inr_cr']
        
        # Check flow filter
        if estimated_flow < self.params['flow_filter_cr']:
            logger.info(f"Skipping trade - flow {estimated_flow} below threshold {self.params['flow_filter_cr']}")
            return
        
        # Calculate entry date
        entry_date = announcement_date + timedelta(days=self.params['entry_days_post_announcement'])
        
        logger.info(f"Rebalance event - Entry planned for {entry_date}")
        
        # Trade added stocks (LONG)
        for ticker in added_stocks:
            symbol = ticker.replace('.NS', '')  # Remove .NS suffix
            self._place_long_trade(symbol, capital)
        
        # Trade removed stocks (SHORT)
        for ticker in removed_stocks:
            symbol = ticker.replace('.NS', '')
            self._place_short_trade(symbol, capital)
    
    def _place_long_trade(self, symbol: str, capital: float):
        """Place long trade for added stock"""
        try:
            # Get current price
            quote = self.market_data.get_ltp([f'NSE:{symbol}'])
            if not quote:
                logger.warning(f"Could not get quote for {symbol}")
                return
            
            ltp = quote[f'NSE:{symbol}']['last_price']
            
            # Calculate position size
            position_value = capital * (self.params['position_size_pct'] / 100)
            quantity = int(position_value / ltp)
            
            if quantity < 1:
                logger.warning(f"Position size too small for {symbol}")
                return
            
            # Place order
            order_id = self.order_manager.place_long_order(
                symbol=symbol,
                quantity=quantity,
                price=ltp * 1.005,  # Limit 0.5% above LTP
                product=self.params['trade_mode']
            )
            
            if order_id:
                # Place stop-loss
                sl_trigger = ltp * (1 - self.params['stop_loss_pct'] / 100)
                sl_price = sl_trigger * 0.995  # 0.5% below trigger
                
                sl_order_id = self.order_manager.place_stop_loss_order(
                    symbol=symbol,
                    quantity=quantity,
                    trigger_price=sl_trigger,
                    price=sl_price,
                    transaction_type='SELL',
                    product=self.params['trade_mode']
                )
                
                # Track trade
                self.active_trades[symbol] = {
                    'direction': 'LONG',
                    'entry_price': ltp,
                    'quantity': quantity,
                    'order_id': order_id,
                    'sl_order_id': sl_order_id,
                    'entry_time': datetime.now()
                }
                
        except Exception as e:
            logger.error(f"Error placing long trade for {symbol}: {e}")
    
    def _place_short_trade(self, symbol: str, capital: float):
        """Place short trade for removed stock"""
        try:
            # Get current price
            quote = self.market_data.get_ltp([f'NSE:{symbol}'])
            if not quote:
                logger.warning(f"Could not get quote for {symbol}")
                return
            
            ltp = quote[f'NSE:{symbol}']['last_price']
            
            # Calculate position size
            position_value = capital * (self.params['position_size_pct'] / 100)
            quantity = int(position_value / ltp)
            
            if quantity < 1:
                logger.warning(f"Position size too small for {symbol}")
                return
            
            # Place order (MIS recommended for shorts)
            order_id = self.order_manager.place_short_order(
                symbol=symbol,
                quantity=quantity,
                price=ltp * 0.995,  # Limit 0.5% below LTP
                product='MIS'  # Shorts typically done intraday
            )
            
            if order_id:
                # Place stop-loss (price rises for shorts)
                sl_trigger = ltp * (1 + self.params['stop_loss_pct'] / 100)
                sl_price = sl_trigger * 1.005  # 0.5% above trigger
                
                sl_order_id = self.order_manager.place_stop_loss_order(
                    symbol=symbol,
                    quantity=quantity,
                    trigger_price=sl_trigger,
                    price=sl_price,
                    transaction_type='BUY',
                    product='MIS'
                )
                
                # Track trade
                self.active_trades[symbol] = {
                    'direction': 'SHORT',
                    'entry_price': ltp,
                    'quantity': quantity,
                    'order_id': order_id,
                    'sl_order_id': sl_order_id,
                    'entry_time': datetime.now()
                }
                
        except Exception as e:
            logger.error(f"Error placing short trade for {symbol}: {e}")
    
    def monitor_and_exit_trades(self, exit_date: datetime):
        """
        Monitor active trades and exit at appropriate time
        
        Args:
            exit_date: Date to exit all positions
        """
        for symbol, trade_info in list(self.active_trades.items()):
            try:
                # Check if exit date reached
                if datetime.now().date() >= exit_date.date():
                    logger.info(f"Exit date reached for {symbol}, closing position")
                    
                    if trade_info['direction'] == 'LONG':
                        self.position_monitor.close_position(
                            symbol=symbol,
                            quantity=trade_info['quantity'],
                            transaction_type='SELL',
                            product=self.params['trade_mode']
                        )
                    else:  # SHORT
                        self.position_monitor.close_position(
                            symbol=symbol,
                            quantity=trade_info['quantity'],
                            transaction_type='BUY',
                            product='MIS'
                        )
                    
                    # Remove from active trades
                    del self.active_trades[symbol]
                    continue
                
                # Check for take-profit
                current_price = self.market_data.get_ltp([f'NSE:{symbol}'])
                if current_price:
                    ltp = current_price[f'NSE:{symbol}']['last_price']
                    entry_price = trade_info['entry_price']
                    
                    if trade_info['direction'] == 'LONG':
                        pnl_pct = (ltp - entry_price) / entry_price * 100
                    else:  # SHORT
                        pnl_pct = (entry_price - ltp) / entry_price * 100
                    
                    if pnl_pct >= self.params['take_profit_pct']:
                        logger.info(f"Take-profit hit for {symbol} ({pnl_pct:.2f}%), closing position")
                        
                        if trade_info['direction'] == 'LONG':
                            self.position_monitor.close_position(
                                symbol=symbol,
                                quantity=trade_info['quantity'],
                                transaction_type='SELL',
                                product=self.params['trade_mode']
                            )
                        else:
                            self.position_monitor.close_position(
                                symbol=symbol,
                                quantity=trade_info['quantity'],
                                transaction_type='BUY',
                                product='MIS'
                            )
                        
                        del self.active_trades[symbol]
                
            except Exception as e:
                logger.error(f"Error monitoring trade for {symbol}: {e}")

# =====================================================
# EXAMPLE USAGE
# =====================================================

def main():
    """Example usage of Zerodha integration"""
    
    # Configuration (replace with your credentials)
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    
    # Initialize bot
    bot = IndexRebalanceTradingBot(
        api_key=API_KEY,
        api_secret=API_SECRET,
        strategy_params={
            'entry_days_post_announcement': 2,
            'exit_days_post_effective': 3,
            'position_size_pct': 2.5,
            'stop_loss_pct': 5.0,
            'take_profit_pct': 10.0,
            'flow_filter_cr': 500,
            'trade_mode': 'CNC'
        }
    )
    
    # For first-time authentication
    if not bot.auth.load_token():
        print(f"Login here: {bot.auth.get_login_url()}")
        request_token = input("Enter request token from redirect URL: ")
        bot.auth.authenticate(request_token)
        bot.auth.save_token()
    
    # Example: Execute trade for a rebalance event
    rebalance_event = {
        'announcement_date': datetime(2025, 1, 31),
        'effective_date': datetime(2025, 3, 31),
        'added_stocks': ['DIXON.NS', 'JSWSTEEL.NS'],
        'removed_stocks': ['HINDALCO.NS', 'UPL.NS'],
        'estimated_aum_inr_cr': 1600
    }
    
    # Execute trades (would be done on entry date)
    # bot.execute_rebalance_trade(rebalance_event, capital=1000000)
    
    # Monitor positions (would be done daily until exit date)
    # bot.monitor_and_exit_trades(exit_date=datetime(2025, 4, 3))
    
    print("Zerodha integration ready for live trading!")

if __name__ == "__main__":
    main()
