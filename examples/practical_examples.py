"""
Practical Examples - Index Rebalancing Strategy
================================================

This file demonstrates practical usage scenarios for the Index Rebalancing strategy.

Run specific examples:
    python examples/practical_examples.py --example <number>

"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import warnings
warnings.filterwarnings('ignore')

from strategies.index_rebalance_frontrun import (
    ZerodhaCharges,
    get_nifty50_rebalance_events,
    ParameterOptimizer,
    calculate_buy_hold_benchmark,
    generate_performance_report
)
import datetime as dt

def example_1_transaction_costs():
    """
    Example 1: Calculate transaction costs for a typical trade
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Transaction Cost Analysis")
    print("="*80)
    
    # Scenario: Buy 10 shares of stock at ₹5000
    price = 5000
    quantity = 10
    turnover = price * quantity  # ₹50,000
    
    print(f"\nTrade Details:")
    print(f"  Stock Price: ₹{price:,}")
    print(f"  Quantity: {quantity}")
    print(f"  Turnover: ₹{turnover:,}")
    
    # CNC (Delivery) - typically for longs
    print(f"\n1. CNC (Delivery) Charges:")
    cnc_buy = ZerodhaCharges.cnc_charges(price, quantity, is_buy=True)
    cnc_sell = ZerodhaCharges.cnc_charges(price, quantity, is_buy=False)
    print(f"   Buy Charges: ₹{cnc_buy:.2f} ({cnc_buy/turnover*100:.3f}% of turnover)")
    print(f"   Sell Charges: ₹{cnc_sell:.2f} ({cnc_sell/turnover*100:.3f}% of turnover)")
    print(f"   Total Round-Trip: ₹{cnc_buy + cnc_sell:.2f} ({(cnc_buy + cnc_sell)/turnover*100:.3f}%)")
    
    # MIS (Intraday) - typically for shorts
    print(f"\n2. MIS (Intraday) Charges:")
    mis_buy = ZerodhaCharges.mis_charges(price, quantity, is_buy=True)
    mis_sell = ZerodhaCharges.mis_charges(price, quantity, is_buy=False)
    print(f"   Buy Charges: ₹{mis_buy:.2f} ({mis_buy/turnover*100:.3f}% of turnover)")
    print(f"   Sell Charges: ₹{mis_sell:.2f} ({mis_sell/turnover*100:.3f}% of turnover)")
    print(f"   Total Round-Trip: ₹{mis_buy + mis_sell:.2f} ({(mis_buy + mis_sell)/turnover*100:.3f}%)")
    
    # Break-even analysis
    print(f"\n3. Break-Even Analysis:")
    cnc_breakeven = (cnc_buy + cnc_sell) / quantity
    mis_breakeven = (mis_buy + mis_sell) / quantity
    print(f"   CNC: Stock must move ₹{cnc_breakeven:.2f} ({cnc_breakeven/price*100:.3f}%) to break even")
    print(f"   MIS: Stock must move ₹{mis_breakeven:.2f} ({mis_breakeven/price*100:.3f}%) to break even")
    
    print("\n" + "="*80)

def example_2_single_rebalance():
    """
    Example 2: Analyze a single historical rebalance event
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Single Rebalance Event Analysis")
    print("="*80)
    
    # Get historical events
    events = get_nifty50_rebalance_events()
    
    # Focus on Dixon Technologies addition (2023)
    dixon_event = events[events['added_stocks'].apply(lambda x: 'DIXON.NS' in x)].iloc[0]
    
    print(f"\nDixon Technologies Addition to Nifty 50")
    print(f"-" * 80)
    print(f"Announcement Date: {dixon_event['announcement_date'].strftime('%Y-%m-%d')}")
    print(f"Effective Date: {dixon_event['effective_date'].strftime('%Y-%m-%d')}")
    print(f"Time Window: {(dixon_event['effective_date'] - dixon_event['announcement_date']).days} days")
    print(f"\nStocks Added: {', '.join(dixon_event['added_stocks'])}")
    print(f"Stocks Removed: {', '.join(dixon_event['removed_stocks'])}")
    print(f"Estimated Fund Flow: ₹{dixon_event['estimated_aum_inr_cr']:,} crores")
    
    # Simulate strategy with optimal parameters
    print(f"\nStrategy Simulation (Optimal Parameters):")
    params = {
        'entry_days_post_announcement': 2,
        'exit_days_post_effective': 3,
        'position_size_pct': 2.5,
        'stop_loss_pct': 5.0,
        'take_profit_pct': 10.0,
        'flow_filter_cr': 500,
        'trade_mode': 'CNC'
    }
    
    entry_date = dixon_event['announcement_date'] + dt.timedelta(days=params['entry_days_post_announcement'])
    exit_date = dixon_event['effective_date'] + dt.timedelta(days=params['exit_days_post_effective'])
    
    print(f"  Entry Date: {entry_date.strftime('%Y-%m-%d')} (2 days post-announcement)")
    print(f"  Exit Date: {exit_date.strftime('%Y-%m-%d')} (3 days post-effective)")
    print(f"  Position Size: {params['position_size_pct']}% per stock")
    print(f"  Stop-Loss: {params['stop_loss_pct']}%")
    print(f"  Take-Profit: {params['take_profit_pct']}%")
    
    # Theoretical trade
    capital = 1000000  # ₹10 lakh
    position_value = capital * (params['position_size_pct'] / 100)  # ₹25,000
    
    print(f"\nExample Trade for DIXON.NS:")
    print(f"  Capital Allocated: ₹{position_value:,.0f}")
    print(f"  Assumed Entry Price: ₹5,000 (hypothetical)")
    print(f"  Quantity: {int(position_value / 5000)} shares")
    print(f"  Target Exit: ₹5,500 (+10%)")
    print(f"  Stop-Loss: ₹4,750 (-5%)")
    
    print("\n" + "="*80)

def example_3_parameter_comparison():
    """
    Example 3: Compare different parameter sets
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Parameter Set Comparison")
    print("="*80)
    
    events = get_nifty50_rebalance_events()
    optimizer = ParameterOptimizer(events, initial_capital=1000000)
    
    # Define three parameter profiles
    profiles = {
        'Conservative': {
            'entry_days_post_announcement': 3,
            'exit_days_post_effective': 2,
            'position_size_pct': 1.5,
            'stop_loss_pct': 4.0,
            'take_profit_pct': 8.0,
            'flow_filter_cr': 600,
            'trade_mode': 'CNC'
        },
        'Balanced': {
            'entry_days_post_announcement': 2,
            'exit_days_post_effective': 3,
            'position_size_pct': 2.5,
            'stop_loss_pct': 5.0,
            'take_profit_pct': 10.0,
            'flow_filter_cr': 500,
            'trade_mode': 'CNC'
        },
        'Aggressive': {
            'entry_days_post_announcement': 1,
            'exit_days_post_effective': 5,
            'position_size_pct': 4.0,
            'stop_loss_pct': 7.0,
            'take_profit_pct': 15.0,
            'flow_filter_cr': 300,
            'trade_mode': 'CNC'
        }
    }
    
    print("\nComparing three parameter profiles...")
    print(f"{'Profile':<15} {'Entry':<8} {'Exit':<8} {'Size':<8} {'SL':<8} {'TP':<8} {'Filter':<10}")
    print("-" * 80)
    
    for name, params in profiles.items():
        print(f"{name:<15} "
              f"{params['entry_days_post_announcement']:<8} "
              f"{params['exit_days_post_effective']:<8} "
              f"{params['position_size_pct']:<8} "
              f"{params['stop_loss_pct']:<8} "
              f"{params['take_profit_pct']:<8} "
              f"₹{params['flow_filter_cr']:<9}cr")
    
    print("\nNote: Full backtest would show performance metrics for each profile.")
    print("Run main strategy file for complete results.")
    
    print("\n" + "="*80)

def example_4_benchmark_comparison():
    """
    Example 4: Compare strategy vs buy-and-hold benchmark
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Strategy vs Buy-and-Hold Benchmark")
    print("="*80)
    
    print("\nCalculating Nifty 50 buy-and-hold performance...")
    
    # Recent 3-year period
    benchmark_3y = calculate_buy_hold_benchmark(
        ticker='^NSEI',
        start_date='2021-01-01',
        end_date='2024-01-01'
    )
    
    print(f"\nNifty 50 Buy-and-Hold (2021-2024):")
    print(f"  Total Return: {benchmark_3y['total_return']:.2f}%")
    print(f"  Annualized Return: {benchmark_3y['annualized_return']:.2f}%")
    print(f"  Max Drawdown: {benchmark_3y['max_drawdown']:.2f}%")
    
    # Strategy target (from optimization)
    print(f"\nIndex Rebalancing Strategy (Target):")
    print(f"  Total Return: ~60-80% (3 years)")
    print(f"  Annualized Return: 18-22%")
    print(f"  Max Drawdown: <15%")
    print(f"  Sharpe Ratio: >2.0")
    
    print(f"\nExpected Outperformance:")
    target_annual = 20  # Mid-range target
    outperformance = target_annual - benchmark_3y['annualized_return']
    print(f"  Strategy vs Benchmark: +{outperformance:.2f}% annualized")
    
    # Compound over time
    print(f"\nGrowth of ₹10 Lakh over 3 years:")
    initial = 1000000
    benchmark_final = initial * (1 + benchmark_3y['annualized_return']/100) ** 3
    strategy_final = initial * (1 + target_annual/100) ** 3
    
    print(f"  Buy-and-Hold: ₹{benchmark_final:,.0f}")
    print(f"  Strategy: ₹{strategy_final:,.0f}")
    print(f"  Additional Gain: ₹{strategy_final - benchmark_final:,.0f}")
    
    print("\n" + "="*80)

def main():
    """Main function to run examples"""
    
    print("\n" + "="*80)
    print("INDEX REBALANCING STRATEGY - PRACTICAL EXAMPLES")
    print("="*80)
    
    examples = {
        '1': ('Transaction Cost Analysis', example_1_transaction_costs),
        '2': ('Single Rebalance Event', example_2_single_rebalance),
        '3': ('Parameter Comparison', example_3_parameter_comparison),
        '4': ('Benchmark Comparison', example_4_benchmark_comparison),
    }
    
    if len(sys.argv) > 1 and sys.argv[1] == '--example':
        if len(sys.argv) > 2:
            example_num = sys.argv[2]
            if example_num in examples:
                examples[example_num][1]()
            else:
                print(f"Invalid example number: {example_num}")
        else:
            print("Please specify example number")
    else:
        # Run all examples
        print("\nAvailable Examples:")
        for num, (name, _) in examples.items():
            print(f"  {num}. {name}")
        
        print("\nRunning all examples...\n")
        for num, (name, func) in examples.items():
            func()
    
    print("\n" + "="*80)
    print("For full strategy execution:")
    print("  python strategies/index_rebalance_frontrun.py")
    print("\nFor detailed documentation:")
    print("  See docs/INDEX_REBALANCE_STRATEGY_GUIDE.md")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
