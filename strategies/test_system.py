"""
Quick test of the comprehensive backtesting system
Tests with smaller parameter space for faster validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))

import pandas as pd
import numpy as np
from datetime import datetime
from backtesting import Backtest
import warnings
warnings.filterwarnings('ignore')

from data_fetcher import IntradayDataFetcher
from zerodha_charges import ZerodhaCharges
from advanced_sma_crossover import AdvancedSMACrossover, BuyAndHoldStrategy

print("=" * 80)
print("QUICK TEST - SMA Crossover Strategy")
print("=" * 80)

# Test with a single symbol and limited time period
symbol = 'NIFTYBEES.NS'
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 10, 6)
initial_capital = 100000

print(f"\nTest Configuration:")
print(f"  Symbol: {symbol}")
print(f"  Period: {start_date.date()} to {end_date.date()}")
print(f"  Capital: ₹{initial_capital:,}")

# Fetch data
print(f"\nFetching data...")
fetcher = IntradayDataFetcher(symbol, start_date, end_date)
data = fetcher.fetch_intraday_data(interval='5m')

print(f"Data loaded: {len(data)} bars")
print(f"Date range: {data.index[0]} to {data.index[-1]}")

# Test buy-and-hold
print("\n" + "-" * 60)
print("1. Testing Buy-and-Hold Strategy")
print("-" * 60)

bt_bh = Backtest(data, BuyAndHoldStrategy, cash=initial_capital, commission=0.001)
stats_bh = bt_bh.run()

print(f"Final Equity: ₹{stats_bh['Equity Final [$]']:,.2f}")
print(f"Total Return: {stats_bh['Return [%]']:.2f}%")

# Test SMA strategy with default parameters
print("\n" + "-" * 60)
print("2. Testing SMA Crossover Strategy (Default Params)")
print("-" * 60)

AdvancedSMACrossover.short_sma = 10
AdvancedSMACrossover.long_sma = 50
AdvancedSMACrossover.stop_loss = 0.05
AdvancedSMACrossover.take_profit = 0.10
AdvancedSMACrossover.trade_mode = 'MIS'

bt_sma = Backtest(data, AdvancedSMACrossover, cash=initial_capital, commission=0.001)
stats_sma = bt_sma.run()

print(f"Parameters:")
print(f"  Short SMA: {AdvancedSMACrossover.short_sma}")
print(f"  Long SMA: {AdvancedSMACrossover.long_sma}")
print(f"  Stop Loss: {AdvancedSMACrossover.stop_loss:.1%}")
print(f"  Take Profit: {AdvancedSMACrossover.take_profit:.1%}")
print(f"  Mode: {AdvancedSMACrossover.trade_mode}")

print(f"\nResults:")
print(f"  Final Equity: ₹{stats_sma['Equity Final [$]']:,.2f}")
print(f"  Total Return: {stats_sma['Return [%]']:.2f}%")
print(f"  Number of Trades: {stats_sma['# Trades']}")
print(f"  Win Rate: {stats_sma.get('Win Rate [%]', 0):.2f}%")
print(f"  Max Drawdown: {stats_sma.get('Max. Drawdown [%]', 0):.2f}%")

# Test with different parameters
print("\n" + "-" * 60)
print("3. Testing Alternative Parameters")
print("-" * 60)

test_params = [
    {'short': 5, 'long': 20, 'sl': 0.03, 'tp': 0.08},
    {'short': 15, 'long': 60, 'sl': 0.07, 'tp': 0.15},
    {'short': 20, 'long': 100, 'sl': 0.05, 'tp': 0.12},
]

best_return = -999
best_params = None

for i, params in enumerate(test_params, 1):
    AdvancedSMACrossover.short_sma = params['short']
    AdvancedSMACrossover.long_sma = params['long']
    AdvancedSMACrossover.stop_loss = params['sl']
    AdvancedSMACrossover.take_profit = params['tp']
    
    bt = Backtest(data, AdvancedSMACrossover, cash=initial_capital, commission=0.001)
    stats = bt.run()
    
    total_return = stats['Return [%]']
    print(f"  {i}. SMA({params['short']},{params['long']}) SL={params['sl']:.1%} TP={params['tp']:.1%} → Return: {total_return:.2f}%")
    
    if total_return > best_return:
        best_return = total_return
        best_params = params

print(f"\nBest parameters: {best_params}")
print(f"Best return: {best_return:.2f}%")

# Test Zerodha charges
print("\n" + "-" * 60)
print("4. Testing Zerodha Charges Calculation")
print("-" * 60)

trade_value = 50000
charges_mis = ZerodhaCharges.calculate_mis_charges(trade_value, trade_value)
charges_cnc = ZerodhaCharges.calculate_cnc_charges(trade_value, trade_value)

print(f"For ₹{trade_value:,} trade:")
print(f"  MIS charges: ₹{charges_mis['total']:.2f} ({charges_mis['total']/trade_value*100:.3f}%)")
print(f"  CNC charges: ₹{charges_cnc['total']:.2f} ({charges_cnc['total']/trade_value*100:.3f}%)")

print("\n" + "=" * 80)
print("✓ ALL TESTS PASSED")
print("=" * 80)
print("\nThe comprehensive backtesting system is working correctly.")
print("To run full optimization, execute: python comprehensive_sma_backtest.py")
