# Algorithmic Trading for Indian Markets 🇮🇳

This repository contains code, strategies, and experiments for algorithmic trading 
in Indian stock markets (NSE, BSE). 

## 🎯 Featured: SMA Crossover Optimization

**NEW!** Comprehensive optimization of SMA crossover strategy with 76,120+ backtests:
- 📊 **Optimal Parameters**: Short SMA=8, Long SMA=20, Max Holding=60 days
- 📈 **Performance**: 18.71% annualized return, 1.15 Sharpe ratio
- 🎲 **Risk**: 15.89% max drawdown, 60% win rate
- 📁 **Location**: `backtests/sma_crossover_optimization/`
- 📖 **Quick Start**: See `backtests/sma_crossover_optimization/QUICKSTART.md`

### Files Available
- `optimization_report.txt` - Comprehensive performance analysis
- `live_trading_strategy.py` - Production-ready implementation
- `optimization_results.json` - Complete optimization data (76,120 backtests)
- `trade_log.csv` - Historical trade records (73 trades over 10 years)
- `optimal_strategy_equity_curve.html` - Interactive visualization

## Repository Structure
- `data/` : Market data (raw & processed)
- `notebooks/` : Jupyter notebooks for research
- `strategies/` : Strategy scripts (SMA, MACD, ATR, etc.)
  - `sma_crossover_optimization.py` - Comprehensive SMA optimization system
- `backtests/` : Backtest results & reports
  - `sma_crossover_optimization/` - Complete optimization results and analysis
- `configs/` : Configurations (symbols, broker settings)
- `utils/` : Helper functions

## Getting Started

### Quick Start with SMA Strategy
```bash
# Install dependencies
pip install backtesting yfinance pandas numpy matplotlib scipy tqdm

# Run the pre-optimized strategy
python strategies/sma_crossover_optimization.py

# Or use the live trading code
cd backtests/sma_crossover_optimization
python live_trading_strategy.py
```

### Key Features
- ✅ Exhaustive parameter optimization (76,120 combinations tested)
- ✅ Walk-forward analysis (in-sample/out-of-sample validation)
- ✅ Cross-asset validation (indices and individual stocks)
- ✅ Sensitivity analysis for parameter robustness
- ✅ Market regime analysis (bull/bear/sideways)
- ✅ Transaction costs and slippage included (0.1% + 0.05%)
- ✅ Production-ready live trading code
- ✅ Comprehensive risk warnings and recommendations
