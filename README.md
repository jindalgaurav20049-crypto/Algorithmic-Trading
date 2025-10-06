# Algorithmic Trading for Indian Markets 🇮🇳

This repository contains advanced algorithmic trading strategies, comprehensive backtesting frameworks, and live trading integration for Indian stock markets (NSE, BSE).

## 🎯 Featured Strategy: SMA Crossover with Zerodha Integration

A production-ready Simple Moving Average crossover strategy with:
- **>1 Million Parameter Combinations** tested
- **Realistic Transaction Costs** (Zerodha 2025 rates)
- **Intraday & Delivery Trading** (MIS and CNC modes)
- **Live Trading Integration** via Kite Connect API
- **Comprehensive Risk Management**

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run example workflow
cd strategies
python example_workflow.py

# Run comprehensive backtest
python comprehensive_sma_backtest.py
```

### 📚 Documentation

- **[Strategy Guide](STRATEGY_README.md)** - Detailed strategy documentation
- **[Implementation Notes](IMPLEMENTATION_NOTES.md)** - Production deployment guide
- **[Example Workflow](strategies/example_workflow.py)** - Step-by-step usage guide

## Structure

- **`strategies/`** - Trading strategy implementations
  - `advanced_sma_crossover.py` - Parameterized SMA strategy
  - `comprehensive_sma_backtest.py` - Main backtesting script
  - `example_workflow.py` - Complete usage example
  - `test_system.py` - Quick system validation
  - `sma_strategy.py`, `macd_strategy.py`, `atr_strategy.py` - Original strategies

- **`utils/`** - Utility modules
  - `zerodha_charges.py` - Transaction cost calculator
  - `data_fetcher.py` - Intraday data fetching
  - `optimizer.py` - Parameter optimization (grid search, genetic algorithms)
  - `kite_integration.py` - Live trading with Kite Connect
  - `walk_forward.py` - Walk-forward validation

- **`backtests/`** - Backtest results & reports
- **`data/`** - Market data (gitignored)
- **`notebooks/`** - Jupyter notebooks for research
- **`configs/`** - Configuration files

## Key Features

### 1. Advanced Parameter Optimization
- Grid search for exhaustive testing
- Genetic algorithms for large parameter spaces
- Parallel processing support
- **Capability**: >1M parameter combinations

### 2. Realistic Transaction Costs
Exact Zerodha charges (2025 rates):
- **MIS (Intraday)**: ~0.05-0.08% per trade
- **CNC (Delivery)**: ~0.13-0.25% per trade
- Includes STT, transaction fees, GST, stamp duty, DP charges

### 3. Risk Management
- Position sizing based on risk percentage
- Stop-loss and take-profit support
- Maximum trades per year filter
- Liquidity filters
- MIS auto-squareoff at 3:20 PM

### 4. Live Trading Integration
- Kite Connect API wrapper
- Real-time data streaming
- Automated order placement
- Position monitoring

### 5. Validation Framework
- Walk-forward validation
- In-sample / out-of-sample testing
- Regime analysis
- Performance degradation tracking

## Performance Metrics

The system calculates comprehensive metrics:
- Annualized returns (compounded)
- Sharpe ratio (with 6.5% risk-free rate)
- Maximum drawdown
- Win rate and average trade
- Trades per year
- Excess return vs buy-and-hold

## Example Results

```python
# Example optimization output
Top Strategy Found:
  Short SMA: 10
  Long SMA: 50
  Stop Loss: 5%
  Take Profit: 10%
  Mode: MIS
  
  Annualized Return: 18.5%
  Sharpe Ratio: 1.85
  Max Drawdown: -12.3%
  Win Rate: 58%
  Trades/Year: 145
  
  Excess Return vs Buy-Hold: +6.2%
```

## Data Sources

- **Yahoo Finance** (via yfinance) - Free, limited historical intraday
- **Kite Connect API** - Real-time and historical data (requires account)
- **NSE Archives** - Official historical data
- **Kaggle Datasets** - Pre-processed NSE datasets

## Requirements

```
Python 3.8+
backtesting
yfinance
pandas
numpy
matplotlib
scipy
scikit-learn
kiteconnect (optional, for live trading)
```

## Getting Started

### 1. Clone Repository
```bash
git clone https://github.com/jindalgaurav20049-crypto/Algorithmic-Trading.git
cd Algorithmic-Trading
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Quick Test
```bash
cd strategies
python test_system.py
```

### 4. Explore Example Workflow
```bash
python example_workflow.py
```

### 5. Run Full Backtest
```bash
python comprehensive_sma_backtest.py
```

## Testing Symbols

- **NIFTYBEES.NS** - Nifty 50 ETF (for index trading)
- **DIXON.NS** - Dixon Technologies (mid-cap stock)
- **RELIANCE.NS**, **INFY.NS**, **HDFCBANK.NS** - Additional test cases

## Live Trading Setup

1. Create Kite Connect app at https://developers.kite.trade/
2. Get API key and secret
3. Generate access token (expires daily at 7:30 AM IST)
4. Use `kite_integration.py` module:

```python
from utils.kite_integration import KiteConnectTrader, LiveSMAStrategy

# Initialize
trader = KiteConnectTrader(api_key='your_key', access_token='your_token')

# Create strategy
strategy = LiveSMAStrategy(
    kite_trader=trader,
    symbol='NIFTYBEES.NS',
    short_sma=10,
    long_sma=50,
    stop_loss=0.05,
    take_profit=0.10,
    trade_mode='MIS'
)

# Run (checks every 5 minutes)
strategy.run(check_interval=300)
```

## Important Warnings

⚠️ **This software is for educational purposes only.**

- Trading involves substantial risk of loss
- Past performance does not guarantee future results
- Test thoroughly in paper trading before live deployment
- Start with small capital
- Understand all risks before trading
- Consult with financial advisors

## Known Limitations

1. **Intraday Data**: yfinance provides only ~60 days of minute data
   - Solution: Use Kite Connect API or paid providers for historical data
   - Current fallback: Simulates intraday bars from daily data

2. **Computational**: Full optimization (>1M combos) takes 6-12 hours
   - Solution: Use parallel processing and cloud compute

3. **Slippage**: Backtests assume perfect execution
   - Real trading will have slippage and partial fills

## Contributing

Contributions welcome! Areas for improvement:
- Additional strategy implementations
- More data source integrations
- Enhanced optimization algorithms
- Real-time monitoring dashboards
- Portfolio-level optimization

## License

MIT License - See LICENSE file for details

## Disclaimer

**IMPORTANT**: This software is provided for educational and research purposes only. The authors are not responsible for any financial losses incurred through the use of this software. Trading in financial markets involves risk and may result in loss of capital. Always perform your own due diligence and consult with qualified financial advisors before making investment decisions.

## References

- [Zerodha Charges](https://zerodha.com/charges)
- [Kite Connect API](https://kite.trade/docs/connect/v3/)
- [NSE India](https://www.nseindia.com/)
- [Backtesting.py](https://kernc.github.io/backtesting.py/)

## Contact

For issues, questions, or contributions, please open an issue on GitHub.

---

**Last Updated**: October 2025  
**Version**: 2.0.0 - Comprehensive SMA Strategy with Zerodha Integration
