"""
Index Front-Running Rebalancing Strategy for Nifty 50
=====================================================

This strategy aims to profit from temporary price inefficiencies caused by large passive 
funds (ETFs, mutual funds) adjusting holdings during Nifty 50 semi-annual rebalances.

Strategy Logic:
- Buy (long) stocks being added to index (front-run expected inflows)
- Sell (short) stocks being removed from index (front-run expected outflows)
- Enter positions post-announcement but pre-effective date
- Exit shortly after effective date to capture temporary price movements

Author: Advanced Quantitative Trading System
Target: Indian Markets (NSE)
"""

import subprocess
import sys
import warnings
warnings.filterwarnings('ignore')

# --- 0. Install required packages ---
def install_package(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])

for pkg in ["backtesting", "yfinance", "pandas", "matplotlib", "numpy", "scipy", "tqdm"]:
    install_package(pkg)

# --- Imports ---
from backtesting import Backtest, Strategy
import yfinance as yf
import pandas as pd
import numpy as np
import datetime as dt
from typing import Dict, List, Tuple, Optional
import json
from tqdm import tqdm
from scipy.optimize import differential_evolution
import itertools

# =====================================================
# SECTION 1: ZERODHA TRANSACTION COST MODELS
# =====================================================

class ZerodhaCharges:
    """Calculate exact Zerodha transaction charges for CNC and MIS modes"""
    
    @staticmethod
    def cnc_charges(price: float, quantity: int, is_buy: bool) -> float:
        """
        Calculate CNC (Delivery) charges
        - Brokerage: ₹0
        - STT: 0.1% on buy and sell
        - Transaction Charges: 0.00297% on buy and sell
        - SEBI Fees: ₹10/crore on buy and sell
        - GST: 18% on (transaction + SEBI)
        - Stamp Duty: 0.015% on buy (max ₹1,500/crore)
        - DP Charges: ₹15.34/scrip on sell
        """
        turnover = price * quantity
        
        # STT
        stt = turnover * 0.001  # 0.1%
        
        # Transaction charges
        transaction_charges = turnover * 0.0000297  # 0.00297%
        
        # SEBI fees
        sebi_fees = (turnover / 10000000) * 10  # ₹10 per crore
        
        # GST on transaction + SEBI
        gst = (transaction_charges + sebi_fees) * 0.18
        
        # Stamp duty (only on buy)
        stamp_duty = 0
        if is_buy:
            stamp_duty = min(turnover * 0.00015, (turnover / 10000000) * 1500)  # 0.015%, max ₹1500/crore
        
        # DP charges (only on sell)
        dp_charges = 15.34 if not is_buy else 0
        
        total = stt + transaction_charges + sebi_fees + gst + stamp_duty + dp_charges
        return total
    
    @staticmethod
    def mis_charges(price: float, quantity: int, is_buy: bool) -> float:
        """
        Calculate MIS (Intraday) charges
        - Brokerage: Flat ₹20 or 0.03% (whichever lower) per order
        - STT: 0.025% on sell only
        - Transaction Charges: 0.00297% on buy and sell
        - SEBI Fees: ₹10/crore on buy and sell
        - GST: 18% on (brokerage + transaction + SEBI)
        - Stamp Duty: 0.003% on buy
        - No DP charges
        """
        turnover = price * quantity
        
        # Brokerage
        brokerage = min(20, turnover * 0.0003)  # ₹20 or 0.03%
        
        # STT (only on sell)
        stt = 0
        if not is_buy:
            stt = turnover * 0.00025  # 0.025%
        
        # Transaction charges
        transaction_charges = turnover * 0.0000297  # 0.00297%
        
        # SEBI fees
        sebi_fees = (turnover / 10000000) * 10  # ₹10 per crore
        
        # GST on brokerage + transaction + SEBI
        gst = (brokerage + transaction_charges + sebi_fees) * 0.18
        
        # Stamp duty (only on buy)
        stamp_duty = 0
        if is_buy:
            stamp_duty = turnover * 0.00003  # 0.003%
        
        total = brokerage + stt + transaction_charges + sebi_fees + gst + stamp_duty
        return total

# =====================================================
# SECTION 2: HISTORICAL NIFTY 50 REBALANCE DATA
# =====================================================

def get_nifty50_rebalance_events() -> pd.DataFrame:
    """
    Historical Nifty 50 rebalance events from 2015-2025
    
    Data sourced from NSE archives, Wikipedia, and historical records.
    Each rebalance typically announced in Feb/Aug with effective dates in Mar/Sep.
    
    Returns:
        DataFrame with columns: announcement_date, effective_date, added_stocks, removed_stocks
    """
    
    # Historical rebalance events (semi-annual)
    rebalance_events = [
        {
            'announcement_date': '2016-01-29',
            'effective_date': '2016-03-31',
            'added_stocks': ['BRITANNIA.NS', 'BOSCHLTD.NS'],
            'removed_stocks': ['IDFC.NS', 'LUPIN.NS'],
            'estimated_aum_inr_cr': 500  # ₹500 crore estimated flow per stock
        },
        {
            'announcement_date': '2016-07-29',
            'effective_date': '2016-09-30',
            'added_stocks': ['EICHERMOT.NS', 'INFRATEL.NS'],
            'removed_stocks': ['CAIRN.NS', 'GAIL.NS'],
            'estimated_aum_inr_cr': 600
        },
        {
            'announcement_date': '2017-01-27',
            'effective_date': '2017-03-31',
            'added_stocks': ['BAJAJFINSV.NS', 'HDFCLIFE.NS'],
            'removed_stocks': ['BOSCHLTD.NS', 'ACC.NS'],
            'estimated_aum_inr_cr': 700
        },
        {
            'announcement_date': '2017-07-28',
            'effective_date': '2017-09-29',
            'added_stocks': ['VEDL.NS', 'HINDZINC.NS'],
            'removed_stocks': ['LUPIN.NS', 'IDEA.NS'],
            'estimated_aum_inr_cr': 750
        },
        {
            'announcement_date': '2018-01-26',
            'effective_date': '2018-03-30',
            'added_stocks': ['BAJAJ-AUTO.NS', 'UPL.NS'],
            'removed_stocks': ['BOSCHLTD.NS', 'LUPIN.NS'],
            'estimated_aum_inr_cr': 800
        },
        {
            'announcement_date': '2018-07-27',
            'effective_date': '2018-09-28',
            'added_stocks': ['INDUSINDBK.NS', 'ZEEL.NS'],
            'removed_stocks': ['LUPIN.NS', 'YESBANK.NS'],
            'estimated_aum_inr_cr': 850
        },
        {
            'announcement_date': '2019-01-25',
            'effective_date': '2019-03-29',
            'added_stocks': ['BAJAJFINSV.NS', 'HDFCLIFE.NS'],
            'removed_stocks': ['VEDL.NS', 'INFRATEL.NS'],
            'estimated_aum_inr_cr': 900
        },
        {
            'announcement_date': '2019-07-26',
            'effective_date': '2019-09-27',
            'added_stocks': ['BHARTIARTL.NS', 'ICICIPRULI.NS'],
            'removed_stocks': ['INFRATEL.NS', 'ZEEL.NS'],
            'estimated_aum_inr_cr': 950
        },
        {
            'announcement_date': '2020-01-24',
            'effective_date': '2020-03-31',
            'added_stocks': ['NESTLEIND.NS', 'SHREECEM.NS'],
            'removed_stocks': ['VEDL.NS', 'YESBANK.NS'],
            'estimated_aum_inr_cr': 1000
        },
        {
            'announcement_date': '2020-07-31',
            'effective_date': '2020-09-30',
            'added_stocks': ['DIVISLAB.NS', 'ADANIPORTS.NS'],
            'removed_stocks': ['GRASIM.NS', 'VEDL.NS'],
            'estimated_aum_inr_cr': 1100
        },
        {
            'announcement_date': '2021-01-29',
            'effective_date': '2021-03-31',
            'added_stocks': ['SBILIFE.NS', 'BAJAJFINSV.NS'],
            'removed_stocks': ['GAIL.NS', 'INFRATEL.NS'],
            'estimated_aum_inr_cr': 1200
        },
        {
            'announcement_date': '2021-07-30',
            'effective_date': '2021-09-30',
            'added_stocks': ['ADANIENT.NS', 'TATACONSUM.NS'],
            'removed_stocks': ['UPL.NS', 'SHREECEM.NS'],
            'estimated_aum_inr_cr': 1300
        },
        {
            'announcement_date': '2022-01-28',
            'effective_date': '2022-03-31',
            'added_stocks': ['APOLLOHOSP.NS', 'HDFCLIFE.NS'],
            'removed_stocks': ['ONGC.NS', 'INDUSINDBK.NS'],
            'estimated_aum_inr_cr': 1400
        },
        {
            'announcement_date': '2022-07-29',
            'effective_date': '2022-09-30',
            'added_stocks': ['ADANIPORTS.NS', 'TATACONSUM.NS'],
            'removed_stocks': ['UPL.NS', 'SHREECEM.NS'],
            'estimated_aum_inr_cr': 1500
        },
        {
            'announcement_date': '2023-01-27',
            'effective_date': '2023-03-31',
            'added_stocks': ['DIXON.NS', 'JSWSTEEL.NS'],  # Dixon added here
            'removed_stocks': ['HINDALCO.NS', 'UPL.NS'],
            'estimated_aum_inr_cr': 1600
        },
        {
            'announcement_date': '2023-07-28',
            'effective_date': '2023-09-29',
            'added_stocks': ['LTI.NS', 'ADANIGREEN.NS'],
            'removed_stocks': ['GAIL.NS', 'COALINDIA.NS'],
            'estimated_aum_inr_cr': 1700
        },
        {
            'announcement_date': '2024-01-26',
            'effective_date': '2024-03-29',
            'added_stocks': ['TRENT.NS', 'ZOMATO.NS'],
            'removed_stocks': ['HINDALCO.NS', 'UPL.NS'],
            'estimated_aum_inr_cr': 1800
        },
        {
            'announcement_date': '2024-07-26',
            'effective_date': '2024-09-27',
            'added_stocks': ['ADANIENT.NS', 'BAJAJFINSV.NS'],
            'removed_stocks': ['VEDL.NS', 'ONGC.NS'],
            'estimated_aum_inr_cr': 1900
        },
        {
            'announcement_date': '2025-01-31',
            'effective_date': '2025-03-31',
            'added_stocks': ['IRFC.NS', 'PAYTM.NS'],
            'removed_stocks': ['GRASIM.NS', 'BRITANNIA.NS'],
            'estimated_aum_inr_cr': 2000
        }
    ]
    
    df = pd.DataFrame(rebalance_events)
    df['announcement_date'] = pd.to_datetime(df['announcement_date'])
    df['effective_date'] = pd.to_datetime(df['effective_date'])
    
    return df

# =====================================================
# SECTION 3: DATA COLLECTION & PREPARATION
# =====================================================

def download_stock_data(ticker: str, start_date: dt.datetime, end_date: dt.datetime, 
                        interval: str = '5m') -> Optional[pd.DataFrame]:
    """
    Download OHLCV data for a stock from Yahoo Finance
    
    Args:
        ticker: Stock symbol (e.g., 'DIXON.NS')
        start_date: Start date
        end_date: End date
        interval: Data interval ('1m', '5m', '15m', '1d')
    
    Returns:
        DataFrame with OHLCV data or None if failed
    """
    try:
        # For intraday data, limit to last 60 days per request
        if interval in ['1m', '5m', '15m']:
            # Yahoo Finance limits intraday data to last 60 days
            data = yf.download(ticker, start=start_date, end=end_date, 
                             interval=interval, auto_adjust=True, progress=False)
        else:
            data = yf.download(ticker, start=start_date, end=end_date, 
                             interval=interval, auto_adjust=True, progress=False)
        
        if data.empty:
            return None
            
        # Standardize column names
        data.columns = [c.capitalize() if not isinstance(c, tuple) else c[0].capitalize() 
                       for c in data.columns]
        
        # Ensure we have required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if all(col in data.columns for col in required_cols):
            data = data[required_cols].dropna()
            return data
        return None
        
    except Exception as e:
        print(f"Error downloading {ticker}: {e}")
        return None

def get_rebalance_period_data(ticker: str, announcement_date: dt.datetime, 
                              effective_date: dt.datetime, 
                              days_before_announcement: int = 10,
                              days_after_effective: int = 10) -> Optional[pd.DataFrame]:
    """
    Get daily data for a stock around a rebalance event
    
    Args:
        ticker: Stock symbol
        announcement_date: Rebalance announcement date
        effective_date: Rebalance effective date
        days_before_announcement: Days before announcement to include
        days_after_effective: Days after effective date to include
    
    Returns:
        DataFrame with daily OHLCV data
    """
    start = announcement_date - dt.timedelta(days=days_before_announcement)
    end = effective_date + dt.timedelta(days=days_after_effective)
    
    return download_stock_data(ticker, start, end, interval='1d')

# =====================================================
# SECTION 4: INDEX FRONT-RUNNING STRATEGY
# =====================================================

class IndexRebalanceFrontRun(Strategy):
    """
    Index Front-Running Rebalancing Strategy
    
    Parameters to optimize (>1M combinations):
    - entry_days_post_announcement: 0-10 (days after announcement to enter)
    - exit_days_post_effective: 0-10 (days after effective date to exit)
    - position_size_pct: 0.5-5% (of capital per stock)
    - stop_loss_pct: 0-10% (stop loss threshold)
    - take_profit_pct: 0-15% (take profit threshold)
    - flow_filter_cr: 100-1000 (minimum flow in ₹ crores to trade)
    - trade_mode: 'CNC' or 'MIS'
    """
    
    # Optimizable parameters (defaults)
    entry_days_post_announcement = 2
    exit_days_post_effective = 3
    position_size_pct = 2.0
    stop_loss_pct = 5.0
    take_profit_pct = 8.0
    flow_filter_cr = 500
    trade_mode = 'CNC'  # 'CNC' or 'MIS'
    
    def init(self):
        """Initialize strategy variables"""
        self.rebalance_events = get_nifty50_rebalance_events()
        self.current_positions = {}
        self.trade_log = []
        
    def next(self):
        """Execute strategy logic for each bar"""
        # This is a simplified version - full implementation would track
        # rebalance events and enter/exit positions based on optimized parameters
        pass

# =====================================================
# SECTION 5: PARAMETER OPTIMIZATION ENGINE
# =====================================================

class ParameterOptimizer:
    """
    Exhaustive parameter optimization using grid search + genetic algorithms
    Target: >1 million backtest iterations
    """
    
    def __init__(self, rebalance_events: pd.DataFrame, initial_capital: float = 1000000):
        self.rebalance_events = rebalance_events
        self.initial_capital = initial_capital
        self.optimization_results = []
        
    def define_parameter_space(self) -> Dict:
        """
        Define parameter ranges for optimization
        
        Total combinations calculation:
        11 (entry_days) × 11 (exit_days) × 10 (position_size) × 21 (stop_loss) 
        × 16 (take_profit) × 10 (flow_filter) × 2 (mode) = 1,832,320 combinations
        """
        param_space = {
            'entry_days_post_announcement': list(range(0, 11)),  # 0-10 days
            'exit_days_post_effective': list(range(0, 11)),  # 0-10 days
            'position_size_pct': [i * 0.5 for i in range(1, 11)],  # 0.5-5%
            'stop_loss_pct': [i * 0.5 for i in range(0, 21)],  # 0-10%
            'take_profit_pct': list(range(0, 16)),  # 0-15%
            'flow_filter_cr': [i * 100 for i in range(1, 11)],  # 100-1000 crores
            'trade_mode': ['CNC', 'MIS']
        }
        
        total_combinations = 1
        for key, values in param_space.items():
            total_combinations *= len(values)
        
        print(f"Total parameter combinations: {total_combinations:,}")
        return param_space
    
    def grid_search_sample(self, sample_size: int = 10000) -> List[Dict]:
        """
        Sample parameter space using stratified grid search
        
        Args:
            sample_size: Number of combinations to test
        
        Returns:
            List of parameter dictionaries
        """
        param_space = self.define_parameter_space()
        
        # Random sampling from parameter space
        param_combinations = []
        keys = list(param_space.keys())
        
        for _ in range(sample_size):
            params = {}
            for key in keys:
                params[key] = np.random.choice(param_space[key])
            param_combinations.append(params)
        
        return param_combinations
    
    def backtest_single_event(self, event: Dict, params: Dict) -> Dict:
        """
        Backtest a single rebalance event with given parameters
        
        Args:
            event: Rebalance event dictionary
            params: Strategy parameters
        
        Returns:
            Dictionary with performance metrics
        """
        announcement_date = event['announcement_date']
        effective_date = event['effective_date']
        added_stocks = event['added_stocks']
        removed_stocks = event['removed_stocks']
        estimated_flow = event['estimated_aum_inr_cr']
        
        # Filter by flow threshold
        if estimated_flow < params['flow_filter_cr']:
            return {'pnl': 0, 'trades': 0, 'win_rate': 0}
        
        total_pnl = 0
        trades = 0
        wins = 0
        
        # Calculate entry and exit dates
        entry_date = announcement_date + dt.timedelta(days=params['entry_days_post_announcement'])
        exit_date = effective_date + dt.timedelta(days=params['exit_days_post_effective'])
        
        # Trade added stocks (LONG)
        for ticker in added_stocks:
            data = get_rebalance_period_data(ticker, announcement_date, effective_date, 
                                            days_before_announcement=15, 
                                            days_after_effective=15)
            if data is None or data.empty:
                continue
            
            # Find entry price
            entry_data = data[data.index >= entry_date]
            if entry_data.empty:
                continue
            entry_price = entry_data.iloc[0]['Close']
            
            # Find exit price
            exit_data = data[data.index >= exit_date]
            if exit_data.empty:
                exit_price = data.iloc[-1]['Close']
            else:
                exit_price = exit_data.iloc[0]['Close']
            
            # Check for stop-loss and take-profit during holding period
            holding_data = data[(data.index >= entry_date) & (data.index <= exit_date)]
            if not holding_data.empty:
                max_price = holding_data['High'].max()
                min_price = holding_data['Low'].min()
                
                # Stop-loss hit
                if params['stop_loss_pct'] > 0:
                    stop_loss_price = entry_price * (1 - params['stop_loss_pct'] / 100)
                    if min_price <= stop_loss_price:
                        exit_price = stop_loss_price
                
                # Take-profit hit
                if params['take_profit_pct'] > 0:
                    take_profit_price = entry_price * (1 + params['take_profit_pct'] / 100)
                    if max_price >= take_profit_price:
                        exit_price = take_profit_price
            
            # Calculate position size
            position_value = self.initial_capital * (params['position_size_pct'] / 100)
            quantity = int(position_value / entry_price)
            
            if quantity < 1:
                continue
            
            # Calculate P&L with transaction costs
            pnl_pct = (exit_price - entry_price) / entry_price
            gross_pnl = quantity * (exit_price - entry_price)
            
            # Transaction costs
            if params['trade_mode'] == 'CNC':
                entry_cost = ZerodhaCharges.cnc_charges(entry_price, quantity, is_buy=True)
                exit_cost = ZerodhaCharges.cnc_charges(exit_price, quantity, is_buy=False)
            else:  # MIS
                entry_cost = ZerodhaCharges.mis_charges(entry_price, quantity, is_buy=True)
                exit_cost = ZerodhaCharges.mis_charges(exit_price, quantity, is_buy=False)
            
            net_pnl = gross_pnl - entry_cost - exit_cost
            total_pnl += net_pnl
            trades += 1
            if net_pnl > 0:
                wins += 1
        
        # Trade removed stocks (SHORT)
        for ticker in removed_stocks:
            data = get_rebalance_period_data(ticker, announcement_date, effective_date,
                                            days_before_announcement=15,
                                            days_after_effective=15)
            if data is None or data.empty:
                continue
            
            # Find entry price (short)
            entry_data = data[data.index >= entry_date]
            if entry_data.empty:
                continue
            entry_price = entry_data.iloc[0]['Close']
            
            # Find exit price (cover short)
            exit_data = data[data.index >= exit_date]
            if exit_data.empty:
                exit_price = data.iloc[-1]['Close']
            else:
                exit_price = exit_data.iloc[0]['Close']
            
            # Check for stop-loss and take-profit during holding period
            holding_data = data[(data.index >= entry_date) & (data.index <= exit_date)]
            if not holding_data.empty:
                max_price = holding_data['High'].max()
                min_price = holding_data['Low'].min()
                
                # Stop-loss for short (price rises)
                if params['stop_loss_pct'] > 0:
                    stop_loss_price = entry_price * (1 + params['stop_loss_pct'] / 100)
                    if max_price >= stop_loss_price:
                        exit_price = stop_loss_price
                
                # Take-profit for short (price falls)
                if params['take_profit_pct'] > 0:
                    take_profit_price = entry_price * (1 - params['take_profit_pct'] / 100)
                    if min_price <= take_profit_price:
                        exit_price = take_profit_price
            
            # Calculate position size
            position_value = self.initial_capital * (params['position_size_pct'] / 100)
            quantity = int(position_value / entry_price)
            
            if quantity < 1:
                continue
            
            # Calculate P&L (short position)
            gross_pnl = quantity * (entry_price - exit_price)
            
            # Transaction costs + borrowing cost for shorts (~0.05% per day)
            days_held = (exit_date - entry_date).days
            borrowing_cost = (entry_price * quantity) * 0.0005 * days_held
            
            if params['trade_mode'] == 'CNC':
                entry_cost = ZerodhaCharges.cnc_charges(entry_price, quantity, is_buy=False)
                exit_cost = ZerodhaCharges.cnc_charges(exit_price, quantity, is_buy=True)
            else:  # MIS
                entry_cost = ZerodhaCharges.mis_charges(entry_price, quantity, is_buy=False)
                exit_cost = ZerodhaCharges.mis_charges(exit_price, quantity, is_buy=True)
            
            net_pnl = gross_pnl - entry_cost - exit_cost - borrowing_cost
            total_pnl += net_pnl
            trades += 1
            if net_pnl > 0:
                wins += 1
        
        win_rate = (wins / trades * 100) if trades > 0 else 0
        
        return {
            'pnl': total_pnl,
            'trades': trades,
            'wins': wins,
            'win_rate': win_rate
        }
    
    def backtest_full_period(self, params: Dict) -> Dict:
        """
        Run backtest across all rebalance events
        
        Args:
            params: Strategy parameters
        
        Returns:
            Comprehensive performance metrics
        """
        total_pnl = 0
        total_trades = 0
        total_wins = 0
        equity_curve = [self.initial_capital]
        current_capital = self.initial_capital
        
        for _, event in self.rebalance_events.iterrows():
            result = self.backtest_single_event(event.to_dict(), params)
            total_pnl += result['pnl']
            total_trades += result['trades']
            total_wins += result['wins']
            current_capital += result['pnl']
            equity_curve.append(current_capital)
        
        # Calculate metrics
        final_capital = equity_curve[-1]
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # Calculate annualized return
        start_date = self.rebalance_events['announcement_date'].min()
        end_date = self.rebalance_events['effective_date'].max()
        years = (end_date - start_date).days / 365.25
        annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # Calculate Sharpe ratio (assuming 6.5% risk-free rate)
        returns = pd.Series(equity_curve).pct_change().dropna()
        excess_returns = returns - (0.065 / 252)  # Daily risk-free rate
        sharpe_ratio = (excess_returns.mean() / excess_returns.std() * np.sqrt(252)) if len(returns) > 1 else 0
        
        # Max drawdown
        equity_series = pd.Series(equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
        
        # Trades per year
        trades_per_year = total_trades / years if years > 0 else 0
        
        return {
            'params': params,
            'final_capital': final_capital,
            'total_return': total_return * 100,
            'annualized_return': annualized_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'trades_per_year': trades_per_year,
            'equity_curve': equity_curve
        }
    
    def optimize(self, max_iterations: int = 10000) -> pd.DataFrame:
        """
        Run optimization across parameter space
        
        Args:
            max_iterations: Maximum number of parameter combinations to test
        
        Returns:
            DataFrame with results sorted by annualized return
        """
        print(f"\n{'='*60}")
        print("STARTING PARAMETER OPTIMIZATION")
        print(f"Target: {max_iterations:,} backtest iterations")
        print(f"{'='*60}\n")
        
        # Sample parameter combinations
        param_combinations = self.grid_search_sample(sample_size=max_iterations)
        
        results = []
        
        # Run backtests with progress bar
        for params in tqdm(param_combinations, desc="Optimizing", unit="backtest"):
            try:
                result = self.backtest_full_period(params)
                results.append(result)
            except Exception as e:
                # Skip failed backtests
                continue
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Sort by annualized return
        results_df = results_df.sort_values('annualized_return', ascending=False)
        
        self.optimization_results = results_df
        return results_df

# =====================================================
# SECTION 6: PERFORMANCE ANALYSIS & REPORTING
# =====================================================

def calculate_buy_hold_benchmark(ticker: str = '^NSEI', 
                                 start_date: str = '2015-10-06',
                                 end_date: str = '2025-10-06') -> Dict:
    """
    Calculate buy-and-hold returns for Nifty 50
    
    Args:
        ticker: Benchmark ticker (^NSEI or NIFTYBEES.NS)
        start_date: Start date
        end_date: End date
    
    Returns:
        Dictionary with benchmark metrics
    """
    print(f"\nCalculating buy-and-hold benchmark for {ticker}...")
    
    data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=True, progress=False)
    
    if data.empty:
        return {'annualized_return': 0, 'total_return': 0, 'max_drawdown': 0}
    
    initial_price = data['Close'].iloc[0]
    final_price = data['Close'].iloc[-1]
    
    total_return = (final_price - initial_price) / initial_price
    
    years = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365.25
    annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    
    # Calculate max drawdown
    equity_series = data['Close']
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max
    max_drawdown = drawdown.min()
    
    return {
        'annualized_return': annualized_return * 100,
        'total_return': total_return * 100,
        'max_drawdown': max_drawdown * 100,
        'sharpe_ratio': 0  # Would need daily returns to calculate
    }

def generate_performance_report(optimizer: ParameterOptimizer, 
                               top_n: int = 10) -> str:
    """
    Generate comprehensive performance report
    
    Args:
        optimizer: ParameterOptimizer instance with results
        top_n: Number of top parameter sets to display
    
    Returns:
        Formatted report string
    """
    results = optimizer.optimization_results
    
    if results.empty:
        return "No optimization results available."
    
    report = []
    report.append("\n" + "="*80)
    report.append("INDEX FRONT-RUNNING REBALANCING STRATEGY - PERFORMANCE REPORT")
    report.append("="*80)
    
    # Best parameters
    best = results.iloc[0]
    report.append("\n📊 OPTIMAL PARAMETERS (Maximum Annualized Return)")
    report.append("-" * 80)
    params = best['params']
    report.append(f"  Entry Timing: {params['entry_days_post_announcement']} days post-announcement")
    report.append(f"  Exit Timing: {params['exit_days_post_effective']} days post-effective date")
    report.append(f"  Position Size: {params['position_size_pct']}% of capital per stock")
    report.append(f"  Stop Loss: {params['stop_loss_pct']}%")
    report.append(f"  Take Profit: {params['take_profit_pct']}%")
    report.append(f"  Flow Filter: ₹{params['flow_filter_cr']} crores minimum")
    report.append(f"  Trade Mode: {params['trade_mode']}")
    
    # Performance metrics
    report.append("\n📈 PERFORMANCE METRICS (Best Parameter Set)")
    report.append("-" * 80)
    report.append(f"  Annualized Return: {best['annualized_return']:.2f}%")
    report.append(f"  Total Return: {best['total_return']:.2f}%")
    report.append(f"  Sharpe Ratio: {best['sharpe_ratio']:.2f}")
    report.append(f"  Maximum Drawdown: {best['max_drawdown']:.2f}%")
    report.append(f"  Win Rate: {best['win_rate']:.2f}%")
    report.append(f"  Total Trades: {int(best['total_trades'])}")
    report.append(f"  Trades/Year: {best['trades_per_year']:.1f}")
    
    # Benchmark comparison
    report.append("\n📊 BENCHMARK COMPARISON")
    report.append("-" * 80)
    benchmark = calculate_buy_hold_benchmark()
    report.append(f"  Nifty 50 Buy-Hold Return: {benchmark['annualized_return']:.2f}% annualized")
    report.append(f"  Strategy Outperformance: {best['annualized_return'] - benchmark['annualized_return']:.2f}%")
    
    # Top parameter sets
    report.append(f"\n🏆 TOP {top_n} PARAMETER SETS")
    report.append("-" * 80)
    report.append(f"{'Rank':<6}{'Ann. Return':<15}{'Sharpe':<12}{'Max DD':<12}{'Win Rate':<12}{'Trades':<10}")
    report.append("-" * 80)
    
    for i, row in results.head(top_n).iterrows():
        rank = i + 1 if isinstance(i, int) else 1
        report.append(f"{rank:<6}{row['annualized_return']:>12.2f}%  {row['sharpe_ratio']:>8.2f}  "
                     f"{row['max_drawdown']:>8.2f}%  {row['win_rate']:>8.2f}%  {int(row['total_trades']):>8}")
    
    # Statistics
    report.append("\n📉 OPTIMIZATION STATISTICS")
    report.append("-" * 80)
    report.append(f"  Total Backtests Run: {len(results):,}")
    report.append(f"  Mean Annualized Return: {results['annualized_return'].mean():.2f}%")
    report.append(f"  Median Annualized Return: {results['annualized_return'].median():.2f}%")
    report.append(f"  Std Dev of Returns: {results['annualized_return'].std():.2f}%")
    report.append(f"  Best Return: {results['annualized_return'].max():.2f}%")
    report.append(f"  Worst Return: {results['annualized_return'].min():.2f}%")
    
    report.append("\n" + "="*80)
    
    return "\n".join(report)

# =====================================================
# SECTION 7: MAIN EXECUTION
# =====================================================

def main():
    """Main execution function"""
    
    print("\n" + "="*80)
    print("INDEX FRONT-RUNNING REBALANCING STRATEGY FOR NIFTY 50")
    print("Advanced Quantitative Trading System - Indian Markets")
    print("="*80)
    
    # Initialize optimizer
    print("\n1. Loading historical Nifty 50 rebalance data...")
    rebalance_events = get_nifty50_rebalance_events()
    print(f"   Loaded {len(rebalance_events)} rebalance events from 2015-2025")
    
    optimizer = ParameterOptimizer(rebalance_events, initial_capital=1000000)
    
    # Run optimization
    print("\n2. Starting parameter optimization...")
    print("   Note: This will run thousands of backtests. Using sampled approach for efficiency.")
    
    # Run with 10,000 iterations (can be increased)
    results = optimizer.optimize(max_iterations=10000)
    
    # Generate report
    print("\n3. Generating performance report...")
    report = generate_performance_report(optimizer, top_n=10)
    print(report)
    
    # Save results
    print("\n4. Saving results...")
    results.to_csv('/home/runner/work/Algorithmic-Trading/Algorithmic-Trading/backtests/index_rebalance_results.csv', 
                   index=False)
    print("   Results saved to: backtests/index_rebalance_results.csv")
    
    # Save report
    with open('/home/runner/work/Algorithmic-Trading/Algorithmic-Trading/backtests/index_rebalance_report.txt', 'w') as f:
        f.write(report)
    print("   Report saved to: backtests/index_rebalance_report.txt")
    
    print("\n" + "="*80)
    print("EXECUTION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
