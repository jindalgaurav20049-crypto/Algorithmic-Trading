# Comprehensive SMA Crossover Strategy with Zerodha Integration

## Overview

This project implements an advanced Simple Moving Average (SMA) crossover strategy for Indian equity markets with comprehensive backtesting, parameter optimization, and live trading integration with Zerodha Kite Connect API.

### Key Features

- **Intraday & Delivery Trading**: Supports both MIS (intraday) and CNC (delivery) modes
- **Realistic Transaction Costs**: Exact Zerodha charges (2025) including STT, transaction fees, GST, stamp duty, DP charges
- **Extensive Optimization**: Framework to test >1 million parameter combinations
- **Multiple Timeframes**: Support for 1min, 5min, 15min, 30min, 60min data
- **Walk-Forward Validation**: In-sample and out-of-sample testing
- **Live Trading**: Kite Connect API integration for automated trading
- **Risk Management**: Stop-loss, take-profit, position sizing
- **Performance Analysis**: Comprehensive metrics and visualizations

## Strategy Description

The SMA crossover strategy generates buy/sell signals based on the crossing of two moving averages:

- **Buy Signal**: When short-term SMA crosses above long-term SMA
- **Sell Signal**: When short-term SMA crosses below long-term SMA

### Parameterization

The strategy includes extensive parameterization for optimization:

1. **Timeframe**: 1min, 3min, 5min, 15min (data interval)
2. **Short-term SMA**: 3-150 periods
3. **Long-term SMA**: 20-400 periods (must be > short SMA)
4. **Stop-loss**: 0-15% (0.25% increments)
5. **Take-profit**: 0-25% (0.5% increments)
6. **Trade Mode**: CNC (delivery) or MIS (intraday)
7. **Entry Window**: 0-30 minutes after signal
8. **Position Size**: 0.5-2% risk per trade

## Project Structure

```
Algorithmic-Trading/
├── strategies/
│   ├── comprehensive_sma_backtest.py  # Main backtest script
│   ├── advanced_sma_crossover.py      # Strategy implementation
│   ├── sma_strategy.py                # Original SMA strategy
│   └── ...
├── utils/
│   ├── data_fetcher.py                # Intraday data fetching
│   ├── zerodha_charges.py             # Transaction cost calculator
│   ├── optimizer.py                   # Parameter optimization framework
│   └── kite_integration.py            # Live trading integration
├── backtests/                         # Results and reports
├── data/                              # Market data (not in repo)
└── README.md                          # This file
```

## Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

Additional packages for advanced features:

```bash
pip install scikit-learn scipy kiteconnect
```

## Usage

### 1. Run Comprehensive Backtest

The main script runs optimization for NIFTYBEES.NS and DIXON.NS:

```bash
cd strategies
python comprehensive_sma_backtest.py
```

This will:
- Fetch intraday data (5-minute bars)
- Calculate buy-and-hold baseline
- Optimize strategy parameters
- Generate performance reports
- Save results to CSV

**Note**: Full optimization (>1M combinations) can take several hours. The script limits to 5,000 combinations per symbol for testing.

### 2. Custom Backtest

```python
from data_fetcher import IntradayDataFetcher
from advanced_sma_crossover import AdvancedSMACrossover
from backtesting import Backtest

# Fetch data
fetcher = IntradayDataFetcher('NIFTYBEES.NS', '2015-10-06', '2025-10-06')
data = fetcher.fetch_intraday_data(interval='5m')

# Configure strategy
AdvancedSMACrossover.short_sma = 10
AdvancedSMACrossover.long_sma = 50
AdvancedSMACrossover.stop_loss = 0.05
AdvancedSMACrossover.take_profit = 0.10
AdvancedSMACrossover.trade_mode = 'MIS'

# Run backtest
bt = Backtest(data, AdvancedSMACrossover, cash=100000, commission=0.001)
stats = bt.run()
print(stats)
bt.plot()
```

### 3. Parameter Optimization

```python
from optimizer import ParameterOptimizer
from advanced_sma_crossover import AdvancedSMACrossover

# Create optimizer
optimizer = ParameterOptimizer(
    data=data,
    strategy_class=AdvancedSMACrossover,
    initial_capital=100000,
    commission=0.001
)

# Define parameter grid
param_grid = {
    'short_sma': range(5, 51, 5),
    'long_sma': range(20, 201, 10),
    'stop_loss': [0.03, 0.05, 0.07, 0.10],
    'take_profit': [0.10, 0.15, 0.20],
    'trade_mode': ['MIS', 'CNC']
}

# Run optimization
results = optimizer.grid_search(param_grid, max_combinations=10000)
print(results.head(10))
```

### 4. Live Trading with Kite Connect

```python
from kite_integration import KiteConnectTrader, LiveSMAStrategy

# Initialize Kite Connect
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
    trade_mode='MIS',
    position_size=0.01
)

# Run strategy (checks every 5 minutes)
strategy.run(check_interval=300)
```

## Zerodha Transaction Charges

The system implements exact Zerodha charges as of 2025:

### CNC (Delivery)
- Brokerage: ₹0
- STT: 0.1% on buy and sell
- Transaction charges: 0.00297% on buy and sell
- SEBI fees: ₹10/crore on buy and sell
- GST: 18% on (transaction + SEBI)
- Stamp duty: 0.015% on buy (max ₹1,500/crore)
- DP charges: ₹15.34/scrip on sell

### MIS (Intraday)
- Brokerage: ₹20 or 0.03% (whichever lower) per order
- STT: 0.025% on sell only
- Transaction charges: 0.00297% on buy and sell
- SEBI fees: ₹10/crore on buy and sell
- GST: 18% on (brokerage + transaction + SEBI)
- Stamp duty: 0.003% on buy
- No DP charges

Example calculation:

```python
from zerodha_charges import ZerodhaCharges

# Calculate MIS charges for ₹50,000 trade
buy_value = 50000
sell_value = 51000
charges = ZerodhaCharges.calculate_mis_charges(buy_value, sell_value)
print(f"Total charges: ₹{charges['total']:.2f}")
print(f"Effective rate: {charges['total']/(buy_value+sell_value)*100:.4f}%")
```

## Data Sources

### Intraday Data

The system attempts to fetch intraday data from:

1. **Yahoo Finance** (yfinance): Limited to last ~60 days for minute data
2. **Simulated Data**: Falls back to simulating intraday bars from daily data

For production use, consider:
- **NSE Official**: Historical data from NSE website
- **Kaggle Datasets**: Pre-processed NSE datasets
- **Paid Providers**: AlphaVantage, Quandl, etc.
- **Zerodha Historical API**: Via Kite Connect

### Handling Data Limitations

Due to yfinance limitations, the current implementation:
- Fetches intraday data in 60-day chunks
- Simulates intraday bars from daily data when needed
- Clearly marks simulated data in outputs

For 10-year historical intraday data (2015-2025), you'll need:
```python
# Use Kite Historical Data API
trader = KiteConnectTrader(api_key, access_token)
instrument_token = trader.get_instrument_token('NIFTYBEES')
data = trader.get_historical_data(
    instrument_token,
    from_date=datetime(2015, 10, 6),
    to_date=datetime(2025, 10, 6),
    interval='5minute'
)
```

## Performance Metrics

The system calculates comprehensive metrics:

- **Annualized Return**: Primary optimization target
- **Sharpe Ratio**: Risk-adjusted return (using 6.5% risk-free rate)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Trades per Year**: Frequency filter (<200 for live trading)
- **Average Trade**: Mean profit/loss per trade
- **Excess Return**: Return above buy-and-hold

## Optimization Strategies

### 1. Grid Search
Exhaustive search of parameter combinations:
- Guarantees finding global optimum (if tested)
- Computationally expensive
- Suitable for parallel processing

### 2. Genetic Algorithm
Evolutionary optimization:
- Faster for large parameter spaces
- May find local optima
- Good for initial exploration

### 3. Hybrid Approach
Recommended workflow:
1. Use genetic algorithm to find promising regions
2. Refine with grid search in those regions
3. Validate with walk-forward testing

## Walk-Forward Validation

Recommended approach for robustness:

```python
# Split data
in_sample = data['2015':'2022']   # 7 years
out_sample = data['2022':'2025']  # 3 years

# Optimize on in-sample
optimizer = ParameterOptimizer(in_sample, AdvancedSMACrossover)
results = optimizer.grid_search(param_grid)
best_params = results.iloc[0]

# Validate on out-of-sample
bt = Backtest(out_sample, AdvancedSMACrossover, cash=100000)
for param, value in best_params.items():
    setattr(AdvancedSMACrossover, param, value)
oos_stats = bt.run()

# Check performance gap
gap = best_params['annualized_return'] - oos_stats['Return (Ann.) [%]']
print(f"Performance gap: {gap:.2f}%")
```

## Risk Management

### Position Sizing
The strategy uses fixed fractional position sizing:
```
Position Size = (Account Equity × Risk Percentage) / (Price × Stop Loss)
```

### Stop-Loss Strategies
1. **Fixed Percentage**: Exit if loss exceeds X%
2. **ATR-Based**: Dynamic based on volatility
3. **Time-Based**: Exit after N bars if no profit

### Constraints
- Maximum 200 trades/year (Zerodha practicality)
- Liquidity filter: >50k shares/day average volume
- MIS auto-squareoff at 3:20 PM

## Known Limitations & Risks

### Data Limitations
- Historical intraday data limited to ~60 days via free sources
- Simulated data is approximate (disclosed in outputs)
- No tick-by-tick data for precise execution modeling

### Model Risks
- **Overfitting**: Excessive optimization can lead to curve-fitting
- **Regime Changes**: Market conditions change over time
- **Slippage**: Real execution may differ from backtests
- **Costs**: Charges may change; system uses 2025 rates

### Technical Risks
- **Data Quality**: Gaps, errors in source data
- **API Limits**: Kite Connect has rate limits (3 req/sec)
- **Connectivity**: Network issues can miss signals

## Best Practices

1. **Start Small**: Test with small capital initially
2. **Paper Trade**: Use demo mode before live trading
3. **Monitor Closely**: Regularly review performance
4. **Stay Updated**: Check for charge changes from Zerodha
5. **Backup Plans**: Have manual override capability
6. **Regular Reoptimization**: Quarterly parameter review
7. **Diversification**: Don't rely on single strategy/stock

## Advanced Features

### Monte Carlo Simulation
```python
# Coming soon: Bootstrap-based confidence intervals
```

### Regime Detection
```python
# Coming soon: Adapt parameters to market regimes
```

### Multi-Asset Optimization
```python
# Coming soon: Portfolio-level optimization
```

## Troubleshooting

### Issue: "No intraday data available"
**Solution**: Falls back to simulated data. For real intraday data, use Kite Historical API or paid providers.

### Issue: "Insufficient data for SMA calculation"
**Solution**: Ensure data length > long_sma parameter.

### Issue: "No strategies outperform buy-and-hold"
**Solution**: Try different parameter ranges or assets. Some markets/periods favor passive investing.

### Issue: "Kite Connect authentication failed"
**Solution**: Check API key/token. Tokens expire daily at 7:30 AM IST.

## Contributing

Contributions welcome! Areas for improvement:
- Additional data sources
- More optimization algorithms (Bayesian, PSO)
- Enhanced risk management
- Real-time monitoring dashboard
- Multi-strategy portfolio

## Disclaimer

**This software is for educational and research purposes only. Trading in securities involves risk of loss. Past performance does not guarantee future results. The authors are not responsible for any financial losses incurred through use of this software. Always consult with a qualified financial advisor before making investment decisions.**

## License

MIT License - See LICENSE file for details

## References

- [Zerodha Charges](https://zerodha.com/charges)
- [Kite Connect API](https://kite.trade/docs/connect/v3/)
- [NSE Official](https://www.nseindia.com/)
- [Backtesting.py Documentation](https://kernc.github.io/backtesting.py/)

## Contact

For issues, questions, or contributions, please open an issue on GitHub.

---

**Last Updated**: October 2025  
**Version**: 1.0.0
