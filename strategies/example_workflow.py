"""
Example Usage: Complete Workflow
Demonstrates how to use all components of the system
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

# Import custom modules
from data_fetcher import IntradayDataFetcher
from zerodha_charges import ZerodhaCharges
from advanced_sma_crossover import AdvancedSMACrossover, BuyAndHoldStrategy
from optimizer import ParameterOptimizer
from walk_forward import WalkForwardValidator

print("=" * 80)
print("COMPREHENSIVE EXAMPLE WORKFLOW")
print("=" * 80)

# ============================================================================
# STEP 1: FETCH DATA
# ============================================================================
print("\nSTEP 1: Fetching Data")
print("-" * 60)

symbol = 'NIFTYBEES.NS'
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 10, 6)

fetcher = IntradayDataFetcher(symbol, start_date, end_date)
data = fetcher.fetch_intraday_data(interval='5m')

print(f"Data loaded: {len(data)} bars")
print(f"Columns: {list(data.columns)}")
print(f"Date range: {data.index[0]} to {data.index[-1]}")

# ============================================================================
# STEP 2: CALCULATE TRANSACTION COSTS
# ============================================================================
print("\n\nSTEP 2: Understanding Transaction Costs")
print("-" * 60)

# Example trade
trade_value = 100000  # ₹1 lakh

print(f"For a ₹{trade_value:,} trade:")

# MIS charges
mis_charges = ZerodhaCharges.calculate_mis_charges(trade_value, trade_value)
print(f"\nMIS (Intraday) Mode:")
print(f"  Brokerage: ₹{mis_charges['brokerage']:.2f}")
print(f"  STT: ₹{mis_charges['stt']:.2f}")
print(f"  Transaction charges: ₹{mis_charges['txn_total']:.2f}")
print(f"  GST: ₹{mis_charges['gst']:.2f}")
print(f"  Total: ₹{mis_charges['total']:.2f} ({mis_charges['total']/trade_value*100:.3f}%)")

# CNC charges
cnc_charges = ZerodhaCharges.calculate_cnc_charges(trade_value, trade_value)
print(f"\nCNC (Delivery) Mode:")
print(f"  Brokerage: ₹{cnc_charges['brokerage']:.2f}")
print(f"  STT: ₹{cnc_charges['stt_total']:.2f}")
print(f"  Transaction charges: ₹{cnc_charges['txn_total']:.2f}")
print(f"  DP charges: ₹{cnc_charges['dp_charges']:.2f}")
print(f"  Total: ₹{cnc_charges['total']:.2f} ({cnc_charges['total']/trade_value*100:.3f}%)")

# ============================================================================
# STEP 3: BASELINE - BUY AND HOLD
# ============================================================================
print("\n\nSTEP 3: Calculate Buy-and-Hold Baseline")
print("-" * 60)

bt_baseline = Backtest(data, BuyAndHoldStrategy, cash=100000, commission=0.001)
stats_baseline = bt_baseline.run()

print(f"Buy-and-Hold Performance:")
print(f"  Final Equity: ₹{stats_baseline['Equity Final [$]']:,.2f}")
print(f"  Total Return: {stats_baseline['Return [%]']:.2f}%")
print(f"  Max Drawdown: {stats_baseline.get('Max. Drawdown [%]', 0):.2f}%")

baseline_return = stats_baseline['Return [%]']

# ============================================================================
# STEP 4: SIMPLE STRATEGY TEST
# ============================================================================
print("\n\nSTEP 4: Test Simple SMA Strategy")
print("-" * 60)

# Configure strategy
AdvancedSMACrossover.short_sma = 10
AdvancedSMACrossover.long_sma = 50
AdvancedSMACrossover.stop_loss = 0.05
AdvancedSMACrossover.take_profit = 0.10
AdvancedSMACrossover.trade_mode = 'MIS'
AdvancedSMACrossover.position_size = 0.01

# Run backtest
bt_simple = Backtest(data, AdvancedSMACrossover, cash=100000, commission=0.001)
stats_simple = bt_simple.run()

print(f"SMA Strategy (10/50):")
print(f"  Final Equity: ₹{stats_simple['Equity Final [$]']:,.2f}")
print(f"  Total Return: {stats_simple['Return [%]']:.2f}%")
print(f"  Number of Trades: {stats_simple['# Trades']}")
print(f"  Win Rate: {stats_simple.get('Win Rate [%]', 0):.2f}%")
print(f"  Max Drawdown: {stats_simple.get('Max. Drawdown [%]', 0):.2f}%")

excess_return = stats_simple['Return [%]'] - baseline_return
print(f"  Excess Return vs Buy-Hold: {excess_return:.2f}%")

# ============================================================================
# STEP 5: PARAMETER OPTIMIZATION
# ============================================================================
print("\n\nSTEP 5: Parameter Optimization (Limited)")
print("-" * 60)

# Create optimizer
optimizer = ParameterOptimizer(
    data=data,
    strategy_class=AdvancedSMACrossover,
    initial_capital=100000,
    commission=0.001
)

# Define small parameter grid for demo
param_grid = {
    'short_sma': [5, 10, 15, 20],
    'long_sma': [40, 50, 60, 80],
    'stop_loss': [0.03, 0.05, 0.07],
    'take_profit': [0.08, 0.10, 0.15],
    'trade_mode': ['MIS'],
    'position_size': [0.01]
}

print("Parameter ranges:")
for key, values in param_grid.items():
    print(f"  {key}: {values}")

total_combos = np.prod([len(v) for v in param_grid.values()])
print(f"\nTotal combinations: {total_combos}")

# Run optimization
print("\nOptimizing...")
results = optimizer.grid_search(param_grid, max_combinations=100, parallel=False)

print(f"\nOptimization complete!")
print(f"Tested: {len(results)} combinations")

# Show top 5
print("\nTop 5 Parameter Sets:")
print("-" * 60)
top_5 = results.head(5)
for i, row in top_5.iterrows():
    print(f"\n{i+1}. SMA({row['short_sma']}/{row['long_sma']}) "
          f"SL={row['stop_loss']:.1%} TP={row['take_profit']:.1%}")
    print(f"   Return: {row['annualized_return']:.2f}% | "
          f"Sharpe: {row['sharpe_ratio']:.2f} | "
          f"Trades: {row['num_trades']}")

# ============================================================================
# STEP 6: VALIDATE BEST PARAMETERS
# ============================================================================
print("\n\nSTEP 6: Validate Best Parameters")
print("-" * 60)

if len(results) > 0:
    best = results.iloc[0]
    
    print("Best parameters found:")
    print(f"  Short SMA: {best['short_sma']}")
    print(f"  Long SMA: {best['long_sma']}")
    print(f"  Stop Loss: {best['stop_loss']:.1%}")
    print(f"  Take Profit: {best['take_profit']:.1%}")
    print(f"  Trade Mode: {best['trade_mode']}")
    
    print(f"\nPerformance:")
    print(f"  Annualized Return: {best['annualized_return']:.2f}%")
    print(f"  Sharpe Ratio: {best['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown: {best['max_drawdown']:.2f}%")
    print(f"  Win Rate: {best['win_rate']:.2f}%")
    print(f"  Trades/Year: {best['trades_per_year']:.1f}")
    
    if best['annualized_return'] > baseline_return:
        print(f"\n✓ Strategy BEATS buy-and-hold by {best['annualized_return'] - baseline_return:.2f}%")
    else:
        print(f"\n✗ Strategy UNDERPERFORMS buy-and-hold by {baseline_return - best['annualized_return']:.2f}%")

# ============================================================================
# STEP 7: WALK-FORWARD VALIDATION
# ============================================================================
print("\n\nSTEP 7: Walk-Forward Validation (Demonstration)")
print("-" * 60)

# Note: This requires more data, so we'll just show the concept
print("Walk-forward validation splits data into rolling windows:")
print("  - Train on historical data to optimize parameters")
print("  - Test on the next period (out-of-sample)")
print("  - Roll forward and repeat")
print("\nThis validates that the strategy generalizes to unseen data.")
print("For production, use the WalkForwardValidator class.")

# ============================================================================
# STEP 8: LIVE TRADING SETUP
# ============================================================================
print("\n\nSTEP 8: Live Trading with Kite Connect")
print("-" * 60)

print("""
To implement live trading:

1. Setup Kite Connect:
   - Get API key from https://developers.kite.trade/
   - Generate access token daily

2. Initialize trader:
   from kite_integration import KiteConnectTrader, LiveSMAStrategy
   
   trader = KiteConnectTrader(api_key='your_key', access_token='your_token')

3. Create live strategy:
   strategy = LiveSMAStrategy(
       kite_trader=trader,
       symbol='NIFTYBEES.NS',
       short_sma=10,
       long_sma=50,
       stop_loss=0.05,
       take_profit=0.10,
       trade_mode='MIS'
   )

4. Run strategy:
   strategy.run(check_interval=300)  # Check every 5 minutes

Important:
- Start with paper trading
- Use small position sizes initially
- Monitor closely during market hours
- MIS positions auto-squareoff at 3:20 PM
""")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("WORKFLOW COMPLETE")
print("=" * 80)

print("\nKey Takeaways:")
print("  1. Data can be fetched from multiple sources (yfinance, Kite API, etc.)")
print("  2. Transaction costs significantly impact returns (MIS: ~0.05%, CNC: ~0.13%)")
print("  3. Buy-and-hold provides a baseline to beat")
print("  4. Parameter optimization helps find best settings")
print("  5. Walk-forward validation prevents overfitting")
print("  6. Live trading requires Kite Connect API integration")

print("\nNext Steps:")
print("  - Run full optimization with more combinations")
print("  - Test on multiple symbols (DIXON.NS, etc.)")
print("  - Implement walk-forward validation")
print("  - Add regime analysis")
print("  - Deploy live trading with proper risk management")

print("\n" + "=" * 80)
