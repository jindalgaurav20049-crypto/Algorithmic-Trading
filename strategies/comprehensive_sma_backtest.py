"""
Comprehensive SMA Crossover Strategy Backtesting System
Implements >1M parameter optimization with Zerodha cost integration
For NIFTYBEES.NS and DIXON.NS (2015-2025)
"""

import subprocess
import sys
import os

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

def install_package(package):
    """Install package if not available"""
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages
for pkg in ["backtesting", "yfinance", "pandas", "matplotlib", "numpy", "scipy", "scikit-learn"]:
    install_package(pkg)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtesting import Backtest
import warnings
warnings.filterwarnings('ignore')

# Import custom modules
from data_fetcher import IntradayDataFetcher
from zerodha_charges import ZerodhaCharges
from advanced_sma_crossover import AdvancedSMACrossover, BuyAndHoldStrategy
from optimizer import ParameterOptimizer

# Configuration
SYMBOLS = ['NIFTYBEES.NS', 'DIXON.NS']
START_DATE = datetime(2015, 10, 6)
END_DATE = datetime(2025, 10, 6)
INITIAL_CAPITAL = 100000  # ₹1 Lakh
RISK_FREE_RATE = 0.065  # 6.5% (Indian G-Sec)

# Optimization parameters
TIMEFRAMES = ['5m']  # Start with 5-minute, can add ['1m', '3m', '15m'] later
SHORT_SMA_RANGE = range(3, 51, 2)  # 3 to 50 (reduced for testing)
LONG_SMA_RANGE = range(20, 201, 5)  # 20 to 200 (reduced for testing)
STOP_LOSS_RANGE = np.arange(0.0, 0.16, 0.01)  # 0% to 15%
TAKE_PROFIT_RANGE = np.arange(0.0, 0.26, 0.02)  # 0% to 25%
TRADE_MODES = ['MIS', 'CNC']
ENTRY_WINDOWS = [0, 5, 10, 15, 20, 25, 30]  # minutes
POSITION_SIZES = np.arange(0.005, 0.021, 0.0025)  # 0.5% to 2%

# Estimate total combinations
estimated_combos = (len(TIMEFRAMES) * len(SHORT_SMA_RANGE) * 
                   len(LONG_SMA_RANGE) * len(STOP_LOSS_RANGE) * 
                   len(TAKE_PROFIT_RANGE) * len(TRADE_MODES) * 
                   len(ENTRY_WINDOWS) * len(POSITION_SIZES))

print("=" * 80)
print("COMPREHENSIVE SMA CROSSOVER STRATEGY BACKTESTING")
print("=" * 80)
print(f"Symbols: {', '.join(SYMBOLS)}")
print(f"Period: {START_DATE.date()} to {END_DATE.date()}")
print(f"Initial Capital: ₹{INITIAL_CAPITAL:,}")
print(f"Estimated Parameter Combinations: {estimated_combos:,}")
print("=" * 80)


def fetch_and_prepare_data(symbol, interval='5m'):
    """
    Fetch and prepare data for a symbol
    
    Args:
        symbol: Stock symbol
        interval: Data interval
        
    Returns:
        DataFrame: Prepared OHLCV data
    """
    print(f"\n{'='*60}")
    print(f"Fetching data for {symbol}")
    print(f"{'='*60}")
    
    fetcher = IntradayDataFetcher(symbol, START_DATE, END_DATE)
    data = fetcher.fetch_intraday_data(interval=interval)
    
    # Add time features
    data = fetcher.add_time_features(data)
    
    # Filter trading hours (9:15 AM - 3:30 PM)
    if hasattr(data.index, 'hour'):
        data = data[(data.index.hour >= 9) & 
                   ((data.index.hour < 15) | 
                    ((data.index.hour == 15) & (data.index.minute <= 30)))]
    
    print(f"Data shape: {data.shape}")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    print(f"Total bars: {len(data):,}")
    
    return data


def calculate_buy_and_hold_performance(data, initial_capital):
    """
    Calculate buy-and-hold performance
    
    Args:
        data: OHLCV DataFrame
        initial_capital: Starting capital
        
    Returns:
        dict: Performance metrics
    """
    print("\nCalculating Buy-and-Hold performance...")
    
    bt = Backtest(data, BuyAndHoldStrategy, cash=initial_capital, commission=0.001)
    stats = bt.run()
    
    # Calculate annualized return
    duration_years = (data.index[-1] - data.index[0]).days / 365.25
    total_return = stats['Return [%]'] / 100
    annualized_return = ((1 + total_return) ** (1 / duration_years) - 1) * 100
    
    results = {
        'strategy': 'Buy-and-Hold',
        'final_equity': float(stats['Equity Final [$]']),
        'total_return': float(stats['Return [%]']),
        'annualized_return': float(annualized_return),
        'max_drawdown': float(stats.get('Max. Drawdown [%]', 0)),
        'num_trades': 1
    }
    
    print(f"  Final Equity: ₹{results['final_equity']:,.2f}")
    print(f"  Total Return: {results['total_return']:.2f}%")
    print(f"  Annualized Return: {results['annualized_return']:.2f}%")
    print(f"  Max Drawdown: {results['max_drawdown']:.2f}%")
    
    return results


def optimize_strategy(data, symbol, max_combinations=10000):
    """
    Optimize strategy parameters
    
    Args:
        data: OHLCV DataFrame
        symbol: Stock symbol
        max_combinations: Maximum combinations to test
        
    Returns:
        DataFrame: Optimization results
    """
    print(f"\n{'='*60}")
    print(f"Optimizing parameters for {symbol}")
    print(f"{'='*60}")
    
    # Calculate commission based on trade mode
    # For now, use MIS commission (more conservative)
    avg_trade_value = INITIAL_CAPITAL * 0.5  # Assume 50% position
    commission_pct = ZerodhaCharges.get_commission_percentage(avg_trade_value, mode='MIS')
    
    print(f"Using commission rate: {commission_pct*100:.4f}%")
    
    # Create optimizer
    optimizer = ParameterOptimizer(
        data=data,
        strategy_class=AdvancedSMACrossover,
        initial_capital=INITIAL_CAPITAL,
        commission=commission_pct
    )
    
    # Build parameter grid (filter out invalid combinations)
    param_grid = {}
    
    # Filter long > short combinations
    valid_combinations = []
    for short in SHORT_SMA_RANGE:
        valid_longs = [long for long in LONG_SMA_RANGE if long > short]
        for long in valid_longs:
            valid_combinations.append((short, long))
    
    if not valid_combinations:
        print("Error: No valid SMA combinations found!")
        return None
    
    # Create separate lists for short and long
    param_grid['short_sma'] = [combo[0] for combo in valid_combinations]
    param_grid['long_sma'] = [combo[1] for combo in valid_combinations]
    param_grid['stop_loss'] = list(STOP_LOSS_RANGE)
    param_grid['take_profit'] = list(TAKE_PROFIT_RANGE)
    param_grid['trade_mode'] = TRADE_MODES
    param_grid['entry_window'] = ENTRY_WINDOWS
    param_grid['position_size'] = list(POSITION_SIZES)
    
    # For faster testing, we'll sample combinations
    print(f"\nRunning grid search (max {max_combinations:,} combinations)...")
    
    # Use parallel processing
    results = optimizer.grid_search(
        param_grid=param_grid,
        max_combinations=max_combinations,
        parallel=False,  # Set to False for easier debugging
        n_workers=4
    )
    
    return results


def analyze_results(results, buy_hold_return, symbol):
    """
    Analyze optimization results
    
    Args:
        results: DataFrame with optimization results
        buy_hold_return: Buy-and-hold annualized return
        symbol: Stock symbol
        
    Returns:
        DataFrame: Filtered and analyzed results
    """
    print(f"\n{'='*60}")
    print(f"Analyzing results for {symbol}")
    print(f"{'='*60}")
    
    if results is None or len(results) == 0:
        print("No valid results found!")
        return None
    
    # Filter: Annualized return > buy-and-hold
    outperformers = results[results['annualized_return'] > buy_hold_return].copy()
    
    print(f"Total combinations tested: {len(results):,}")
    print(f"Strategies beating buy-and-hold: {len(outperformers):,}")
    
    if len(outperformers) == 0:
        print("No strategies outperformed buy-and-hold!")
        print("\nTop 5 strategies by annualized return:")
        print(results.head(5)[['short_sma', 'long_sma', 'stop_loss', 'take_profit', 
                              'trade_mode', 'annualized_return', 'sharpe_ratio', 
                              'max_drawdown', 'win_rate', 'trades_per_year']])
        return results.head(5)
    
    # Filter: Trades per year <= 200
    outperformers = outperformers[outperformers['trades_per_year'] <= 200]
    
    print(f"After filtering (<200 trades/year): {len(outperformers):,}")
    
    if len(outperformers) == 0:
        print("No strategies passed the trade frequency filter!")
        return None
    
    # Calculate additional metrics
    outperformers['excess_return'] = outperformers['annualized_return'] - buy_hold_return
    outperformers['risk_adjusted_return'] = (outperformers['annualized_return'] / 
                                             outperformers['max_drawdown'].abs())
    
    # Sort by annualized return
    outperformers = outperformers.sort_values('annualized_return', ascending=False)
    
    print(f"\nTop 10 strategies:")
    print("-" * 60)
    
    display_cols = ['short_sma', 'long_sma', 'stop_loss', 'take_profit', 'trade_mode',
                   'annualized_return', 'excess_return', 'sharpe_ratio', 
                   'max_drawdown', 'win_rate', 'trades_per_year']
    
    print(outperformers.head(10)[display_cols].to_string())
    
    return outperformers


def run_comprehensive_backtest(symbol, max_combinations=5000):
    """
    Run comprehensive backtest for a symbol
    
    Args:
        symbol: Stock symbol
        max_combinations: Maximum parameter combinations to test
        
    Returns:
        tuple: (best_results, all_results, buy_hold_results)
    """
    # Fetch data
    data = fetch_and_prepare_data(symbol, interval='5m')
    
    if data is None or len(data) < 100:
        print(f"Insufficient data for {symbol}")
        return None, None, None
    
    # Calculate buy-and-hold
    buy_hold_results = calculate_buy_and_hold_performance(data, INITIAL_CAPITAL)
    buy_hold_return = buy_hold_results['annualized_return']
    
    # Optimize
    optimization_results = optimize_strategy(data, symbol, max_combinations)
    
    if optimization_results is None:
        return None, None, buy_hold_results
    
    # Analyze
    best_results = analyze_results(optimization_results, buy_hold_return, symbol)
    
    return best_results, optimization_results, buy_hold_results


def generate_report(results_dict):
    """
    Generate comprehensive report
    
    Args:
        results_dict: Dictionary with results for each symbol
    """
    print("\n" + "=" * 80)
    print("COMPREHENSIVE BACKTEST REPORT")
    print("=" * 80)
    
    for symbol, (best_results, all_results, buy_hold) in results_dict.items():
        print(f"\n{'='*60}")
        print(f"SYMBOL: {symbol}")
        print(f"{'='*60}")
        
        if buy_hold:
            print(f"\nBuy-and-Hold Performance:")
            print(f"  Annualized Return: {buy_hold['annualized_return']:.2f}%")
            print(f"  Max Drawdown: {buy_hold['max_drawdown']:.2f}%")
        
        if best_results is not None and len(best_results) > 0:
            print(f"\nBest Strategy:")
            best = best_results.iloc[0]
            print(f"  Short SMA: {best['short_sma']}")
            print(f"  Long SMA: {best['long_sma']}")
            print(f"  Stop Loss: {best['stop_loss']:.2%}")
            print(f"  Take Profit: {best['take_profit']:.2%}")
            print(f"  Trade Mode: {best['trade_mode']}")
            print(f"  Entry Window: {best['entry_window']} minutes")
            print(f"  Position Size: {best['position_size']:.2%}")
            print(f"\n  Performance:")
            print(f"    Annualized Return: {best['annualized_return']:.2f}%")
            print(f"    Sharpe Ratio: {best['sharpe_ratio']:.2f}")
            print(f"    Max Drawdown: {best['max_drawdown']:.2f}%")
            print(f"    Win Rate: {best['win_rate']:.2f}%")
            print(f"    Trades/Year: {best['trades_per_year']:.1f}")
            
            if buy_hold:
                excess = best['annualized_return'] - buy_hold['annualized_return']
                print(f"    Excess Return vs Buy-Hold: {excess:.2f}%")
        else:
            print("\nNo strategies found that outperform buy-and-hold")
    
    print("\n" + "=" * 80)


def main():
    """Main execution function"""
    
    print("\nStarting comprehensive backtest...")
    print(f"This will test up to {estimated_combos:,} parameter combinations")
    print("Note: Full optimization may take several hours")
    print("\nFor testing purposes, we'll limit to 5,000 combinations per symbol\n")
    
    results_dict = {}
    
    for symbol in SYMBOLS:
        try:
            best, all_results, buy_hold = run_comprehensive_backtest(
                symbol, 
                max_combinations=5000
            )
            results_dict[symbol] = (best, all_results, buy_hold)
            
            # Save results
            if best is not None and len(best) > 0:
                output_file = f"/home/runner/work/Algorithmic-Trading/Algorithmic-Trading/backtests/{symbol.replace('.', '_')}_results.csv"
                best.to_csv(output_file, index=False)
                print(f"\nResults saved to: {output_file}")
        
        except Exception as e:
            print(f"\nError processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            results_dict[symbol] = (None, None, None)
    
    # Generate report
    generate_report(results_dict)
    
    print("\n" + "=" * 80)
    print("BACKTEST COMPLETE")
    print("=" * 80)
    print("\nNote: For production use, increase max_combinations and add:")
    print("  - Walk-forward validation")
    print("  - Robustness testing across market regimes")
    print("  - Monte Carlo simulations")
    print("  - Live trading integration with Kite Connect API")


if __name__ == "__main__":
    main()
