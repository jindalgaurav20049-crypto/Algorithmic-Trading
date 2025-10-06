"""
Walk-Forward Validation Module
Implements rolling window optimization and out-of-sample testing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtesting import Backtest
import warnings
warnings.filterwarnings('ignore')

class WalkForwardValidator:
    """
    Perform walk-forward validation for strategy robustness testing
    """
    
    def __init__(self, data, strategy_class, initial_capital=100000, commission=0.001):
        """
        Initialize walk-forward validator
        
        Args:
            data: Full dataset with datetime index
            strategy_class: Strategy class to validate
            initial_capital: Starting capital
            commission: Commission rate
        """
        self.data = data
        self.strategy_class = strategy_class
        self.initial_capital = initial_capital
        self.commission = commission
        
    def split_data(self, in_sample_years=7, out_sample_years=3):
        """
        Split data into in-sample and out-of-sample periods
        
        Args:
            in_sample_years: Years for optimization
            out_sample_years: Years for validation
            
        Returns:
            tuple: (in_sample_data, out_sample_data)
        """
        total_days = (self.data.index[-1] - self.data.index[0]).days
        in_sample_days = int(in_sample_years * 365.25)
        
        split_date = self.data.index[0] + timedelta(days=in_sample_days)
        
        in_sample = self.data[self.data.index < split_date]
        out_sample = self.data[self.data.index >= split_date]
        
        print(f"Data split:")
        print(f"  In-sample: {in_sample.index[0]} to {in_sample.index[-1]} ({len(in_sample)} bars)")
        print(f"  Out-of-sample: {out_sample.index[0]} to {out_sample.index[-1]} ({len(out_sample)} bars)")
        
        return in_sample, out_sample
    
    def rolling_window_split(self, window_size_months=24, step_size_months=3):
        """
        Create rolling windows for walk-forward analysis
        
        Args:
            window_size_months: Size of each training window
            step_size_months: Step size for rolling
            
        Returns:
            list: List of (train_data, test_data) tuples
        """
        windows = []
        
        start_date = self.data.index[0]
        end_date = self.data.index[-1]
        
        current_date = start_date
        
        while current_date < end_date:
            # Training window
            train_start = current_date
            train_end = current_date + timedelta(days=window_size_months * 30)
            
            # Test window (next period)
            test_start = train_end
            test_end = train_end + timedelta(days=step_size_months * 30)
            
            if test_end > end_date:
                test_end = end_date
            
            # Extract data
            train_data = self.data[(self.data.index >= train_start) & (self.data.index < train_end)]
            test_data = self.data[(self.data.index >= test_start) & (self.data.index < test_end)]
            
            if len(train_data) > 0 and len(test_data) > 0:
                windows.append({
                    'train': train_data,
                    'test': test_data,
                    'train_start': train_start,
                    'train_end': train_end,
                    'test_start': test_start,
                    'test_end': test_end
                })
            
            # Move to next window
            current_date += timedelta(days=step_size_months * 30)
        
        print(f"Created {len(windows)} rolling windows")
        return windows
    
    def validate(self, best_params, out_sample_data):
        """
        Validate parameters on out-of-sample data
        
        Args:
            best_params: Dictionary of optimized parameters
            out_sample_data: Out-of-sample dataset
            
        Returns:
            dict: Validation results
        """
        # Set parameters
        for param, value in best_params.items():
            if hasattr(self.strategy_class, param):
                setattr(self.strategy_class, param, value)
        
        # Run backtest
        bt = Backtest(out_sample_data, self.strategy_class,
                     cash=self.initial_capital,
                     commission=self.commission)
        
        stats = bt.run()
        
        # Calculate duration
        duration_years = (out_sample_data.index[-1] - out_sample_data.index[0]).days / 365.25
        
        # Extract metrics
        results = {
            'final_equity': float(stats['Equity Final [$]']),
            'total_return': float(stats['Return [%]']),
            'annualized_return': float(stats.get('Return (Ann.) [%]', 0)),
            'sharpe_ratio': float(stats.get('Sharpe Ratio', 0)),
            'max_drawdown': float(stats.get('Max. Drawdown [%]', 0)),
            'win_rate': float(stats.get('Win Rate [%]', 0)),
            'num_trades': int(stats.get('# Trades', 0)),
            'trades_per_year': int(stats.get('# Trades', 0)) / duration_years if duration_years > 0 else 0
        }
        
        return results
    
    def calculate_degradation(self, in_sample_results, out_sample_results):
        """
        Calculate performance degradation from in-sample to out-of-sample
        
        Args:
            in_sample_results: In-sample performance dict
            out_sample_results: Out-of-sample performance dict
            
        Returns:
            dict: Degradation metrics
        """
        degradation = {}
        
        # Return degradation
        is_return = in_sample_results.get('annualized_return', 0)
        oos_return = out_sample_results.get('annualized_return', 0)
        degradation['return_degradation'] = is_return - oos_return
        degradation['return_degradation_pct'] = (degradation['return_degradation'] / is_return * 100) if is_return != 0 else 0
        
        # Sharpe degradation
        is_sharpe = in_sample_results.get('sharpe_ratio', 0)
        oos_sharpe = out_sample_results.get('sharpe_ratio', 0)
        degradation['sharpe_degradation'] = is_sharpe - oos_sharpe
        
        # Win rate degradation
        is_wr = in_sample_results.get('win_rate', 0)
        oos_wr = out_sample_results.get('win_rate', 0)
        degradation['winrate_degradation'] = is_wr - oos_wr
        
        # Check if acceptable (< 3% return degradation)
        degradation['acceptable'] = abs(degradation['return_degradation']) < 3.0
        
        return degradation
    
    def run_walk_forward(self, param_ranges, window_size_months=24, step_size_months=3,
                        optimize_func=None):
        """
        Run complete walk-forward analysis
        
        Args:
            param_ranges: Parameter ranges for optimization
            window_size_months: Training window size
            step_size_months: Rolling step size
            optimize_func: Function to optimize parameters (should return best params dict)
            
        Returns:
            DataFrame: Walk-forward results
        """
        if optimize_func is None:
            raise ValueError("optimize_func is required")
        
        # Create rolling windows
        windows = self.rolling_window_split(window_size_months, step_size_months)
        
        results = []
        
        for i, window in enumerate(windows):
            print(f"\nProcessing window {i+1}/{len(windows)}")
            print(f"  Train: {window['train_start'].date()} to {window['train_end'].date()}")
            print(f"  Test: {window['test_start'].date()} to {window['test_end'].date()}")
            
            # Optimize on training data
            print("  Optimizing...")
            best_params = optimize_func(window['train'], param_ranges)
            
            # Validate on test data
            print("  Validating...")
            test_results = self.validate(best_params, window['test'])
            
            # Store results
            result = {
                'window': i + 1,
                'train_start': window['train_start'],
                'train_end': window['train_end'],
                'test_start': window['test_start'],
                'test_end': window['test_end'],
                **best_params,
                **test_results
            }
            
            results.append(result)
            
            print(f"  Test Return: {test_results['annualized_return']:.2f}%")
            print(f"  Test Sharpe: {test_results['sharpe_ratio']:.2f}")
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Summary statistics
        print("\n" + "=" * 60)
        print("Walk-Forward Summary")
        print("=" * 60)
        print(f"Windows analyzed: {len(results_df)}")
        print(f"Average OOS return: {results_df['annualized_return'].mean():.2f}%")
        print(f"Median OOS return: {results_df['annualized_return'].median():.2f}%")
        print(f"Std OOS return: {results_df['annualized_return'].std():.2f}%")
        print(f"Average Sharpe: {results_df['sharpe_ratio'].mean():.2f}")
        print(f"Win rate: {(results_df['annualized_return'] > 0).sum() / len(results_df) * 100:.1f}%")
        
        return results_df


def regime_analysis(data, regimes):
    """
    Analyze strategy performance across different market regimes
    
    Args:
        data: Full dataset
        regimes: List of (start_date, end_date, name) tuples
        
    Returns:
        DataFrame: Performance by regime
    """
    results = []
    
    for start, end, name in regimes:
        regime_data = data[(data.index >= start) & (data.index <= end)]
        
        if len(regime_data) > 0:
            # Calculate regime characteristics
            returns = regime_data['Close'].pct_change()
            
            regime_stats = {
                'regime': name,
                'start': start,
                'end': end,
                'days': len(regime_data),
                'total_return': ((regime_data['Close'].iloc[-1] / regime_data['Close'].iloc[0]) - 1) * 100,
                'volatility': returns.std() * np.sqrt(252) * 100,
                'avg_volume': regime_data['Volume'].mean()
            }
            
            results.append(regime_stats)
    
    return pd.DataFrame(results)
