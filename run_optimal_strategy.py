"""
Run Index Rebalancing Strategy with Optimal Parameters on NSEI
===============================================================

This script executes the strategy with optimal parameters and displays detailed results.
"""

import sys
sys.path.insert(0, '/home/runner/work/Algorithmic-Trading/Algorithmic-Trading')

import warnings
warnings.filterwarnings('ignore')

from strategies.index_rebalance_frontrun import (
    get_nifty50_rebalance_events,
    ParameterOptimizer,
    calculate_buy_hold_benchmark
)
import pandas as pd
import numpy as np

def run_optimal_strategy():
    """Run strategy with optimal parameters"""
    
    print("\n" + "="*80)
    print("INDEX REBALANCING STRATEGY - OPTIMAL PARAMETERS BACKTEST")
    print("="*80)
    
    # Load rebalance events
    print("\n1. Loading historical Nifty 50 rebalance data...")
    rebalance_events = get_nifty50_rebalance_events()
    print(f"   ✓ Loaded {len(rebalance_events)} rebalance events (2015-2025)")
    
    # Initialize optimizer
    initial_capital = 1000000  # ₹10 lakhs
    optimizer = ParameterOptimizer(rebalance_events, initial_capital=initial_capital)
    
    # Optimal parameters (from optimization research)
    optimal_params = {
        'entry_days_post_announcement': 2,
        'exit_days_post_effective': 3,
        'position_size_pct': 2.5,
        'stop_loss_pct': 5.0,
        'take_profit_pct': 10.0,
        'flow_filter_cr': 500,
        'trade_mode': 'CNC'
    }
    
    print("\n2. Running backtest with optimal parameters...")
    print("   " + "-"*76)
    print(f"   Entry Timing:        {optimal_params['entry_days_post_announcement']} days post-announcement")
    print(f"   Exit Timing:         {optimal_params['exit_days_post_effective']} days post-effective date")
    print(f"   Position Size:       {optimal_params['position_size_pct']}% per stock")
    print(f"   Stop-Loss:           {optimal_params['stop_loss_pct']}%")
    print(f"   Take-Profit:         {optimal_params['take_profit_pct']}%")
    print(f"   Flow Filter:         ₹{optimal_params['flow_filter_cr']} crores")
    print(f"   Trade Mode:          {optimal_params['trade_mode']}")
    print("   " + "-"*76)
    
    # Run backtest
    result = optimizer.backtest_full_period(optimal_params)
    
    # Calculate benchmark
    print("\n3. Calculating Nifty 50 buy-and-hold benchmark...")
    benchmark = calculate_buy_hold_benchmark(
        ticker='^NSEI',
        start_date='2015-10-06',
        end_date='2025-10-06'
    )
    
    # Display results
    print("\n" + "="*80)
    print("STRATEGY PERFORMANCE RESULTS")
    print("="*80)
    
    print("\n📊 OPTIMAL PARAMETERS BACKTEST RESULTS")
    print("-"*80)
    print(f"Initial Capital:         ₹{initial_capital:,}")
    print(f"Final Capital:           ₹{result['final_capital']:,.2f}")
    print(f"Total Return:            {result['total_return']:.2f}%")
    print(f"Annualized Return:       {result['annualized_return']:.2f}%")
    print(f"Sharpe Ratio:            {result['sharpe_ratio']:.2f}")
    print(f"Maximum Drawdown:        {result['max_drawdown']:.2f}%")
    print(f"Win Rate:                {result['win_rate']:.2f}%")
    print(f"Total Trades:            {int(result['total_trades'])}")
    print(f"Trades per Year:         {result['trades_per_year']:.1f}")
    
    print("\n📈 NIFTY 50 BUY-AND-HOLD BENCHMARK")
    print("-"*80)
    print(f"Annualized Return:       {benchmark['annualized_return']:.2f}%")
    print(f"Total Return:            {benchmark['total_return']:.2f}%")
    print(f"Maximum Drawdown:        {benchmark['max_drawdown']:.2f}%")
    
    print("\n🎯 STRATEGY VS BENCHMARK")
    print("-"*80)
    outperformance = result['annualized_return'] - benchmark['annualized_return']
    print(f"Annualized Outperformance: {outperformance:+.2f}%")
    print(f"Strategy Sharpe Ratio:     {result['sharpe_ratio']:.2f}")
    
    # Additional analysis
    print("\n💰 CAPITAL GROWTH ANALYSIS")
    print("-"*80)
    strategy_growth = (result['final_capital'] / initial_capital - 1) * 100
    benchmark_growth = benchmark['total_return']
    
    print(f"Strategy Growth:         {strategy_growth:+.2f}% (₹{initial_capital:,} → ₹{result['final_capital']:,.0f})")
    print(f"Benchmark Growth:        {benchmark_growth:+.2f}%")
    print(f"Excess Profit:           ₹{result['final_capital'] - initial_capital * (1 + benchmark_growth/100):,.0f}")
    
    # Risk-adjusted metrics
    print("\n⚖️ RISK-ADJUSTED PERFORMANCE")
    print("-"*80)
    print(f"Return per Unit of Risk (Sharpe): {result['sharpe_ratio']:.2f}x")
    print(f"Return / Max Drawdown:            {abs(result['annualized_return'] / result['max_drawdown']):.2f}x")
    
    # Trading activity
    print("\n📊 TRADING ACTIVITY")
    print("-"*80)
    years = (rebalance_events['effective_date'].max() - rebalance_events['announcement_date'].min()).days / 365.25
    print(f"Backtest Period:         {years:.1f} years")
    print(f"Total Rebalance Events:  {len(rebalance_events)}")
    print(f"Total Trades Executed:   {int(result['total_trades'])}")
    print(f"Avg Trades per Event:    {result['total_trades'] / len(rebalance_events):.1f}")
    print(f"Winning Trades:          {int(result['total_trades'] * result['win_rate'] / 100)}")
    print(f"Losing Trades:           {int(result['total_trades'] * (1 - result['win_rate'] / 100))}")
    
    # Equity curve summary
    print("\n📉 EQUITY CURVE SUMMARY")
    print("-"*80)
    equity_series = pd.Series(result['equity_curve'])
    returns = equity_series.pct_change().dropna()
    
    print(f"Starting Equity:         ₹{equity_series.iloc[0]:,.2f}")
    print(f"Ending Equity:           ₹{equity_series.iloc[-1]:,.2f}")
    print(f"Peak Equity:             ₹{equity_series.max():,.2f}")
    print(f"Average Return per Trade: {returns.mean() * 100:.2f}%")
    print(f"Std Dev of Returns:      {returns.std() * 100:.2f}%")
    print(f"Best Trade:              {returns.max() * 100:+.2f}%")
    print(f"Worst Trade:             {returns.min() * 100:+.2f}%")
    
    # Save detailed results
    print("\n4. Saving detailed results...")
    
    results_df = pd.DataFrame([{
        'parameter_set': 'optimal',
        'initial_capital': initial_capital,
        'final_capital': result['final_capital'],
        'total_return_pct': result['total_return'],
        'annualized_return_pct': result['annualized_return'],
        'sharpe_ratio': result['sharpe_ratio'],
        'max_drawdown_pct': result['max_drawdown'],
        'win_rate_pct': result['win_rate'],
        'total_trades': result['total_trades'],
        'trades_per_year': result['trades_per_year'],
        'benchmark_return_pct': benchmark['annualized_return'],
        'outperformance_pct': outperformance,
        **optimal_params
    }])
    
    results_df.to_csv('/home/runner/work/Algorithmic-Trading/Algorithmic-Trading/backtests/optimal_strategy_results.csv', index=False)
    print("   ✓ Results saved to: backtests/optimal_strategy_results.csv")
    
    # Save equity curve
    equity_df = pd.DataFrame({
        'period': range(len(result['equity_curve'])),
        'equity': result['equity_curve']
    })
    equity_df.to_csv('/home/runner/work/Algorithmic-Trading/Algorithmic-Trading/backtests/optimal_equity_curve.csv', index=False)
    print("   ✓ Equity curve saved to: backtests/optimal_equity_curve.csv")
    
    print("\n" + "="*80)
    print("✅ BACKTEST COMPLETE")
    print("="*80)
    print("\nSummary:")
    print(f"  • Strategy achieved {result['annualized_return']:.2f}% annualized return")
    print(f"  • Outperformed Nifty 50 by {outperformance:+.2f}% per year")
    print(f"  • Sharpe ratio of {result['sharpe_ratio']:.2f} indicates strong risk-adjusted returns")
    print(f"  • Win rate of {result['win_rate']:.2f}% across {int(result['total_trades'])} trades")
    print(f"  • Maximum drawdown limited to {result['max_drawdown']:.2f}%")
    print("\n" + "="*80)
    
    return result, benchmark

if __name__ == "__main__":
    try:
        result, benchmark = run_optimal_strategy()
    except Exception as e:
        print(f"\n❌ Error during backtest: {e}")
        import traceback
        traceback.print_exc()
