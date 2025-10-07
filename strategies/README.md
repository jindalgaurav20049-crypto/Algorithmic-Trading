# Strategies

Contains algorithmic trading strategies (Python scripts).

## Available Strategies

### 1. SMA Strategy (`sma_strategy.py`)
Multi-timeframe SMA (Simple Moving Average) trend-following strategy with margin-safe position sizing and trailing stop-loss.

### 2. MACD Strategy (`macd_strategy.py`)
MACD (Moving Average Convergence Divergence) momentum strategy with optimized parameters for Nifty 50.

### 3. ATR Breakout Strategy (`atr_strategy.py`)
ATR (Average True Range) based breakout strategy with dynamic position sizing.

### 4. **Index Rebalancing Front-Run Strategy** (`index_rebalance_frontrun.py`) **[NEW]**
Advanced quantitative strategy targeting temporary price inefficiencies during Nifty 50 semi-annual rebalances.

**Key Features:**
- Anticipates and trades ahead of passive fund rebalances
- Long positions on stocks being added to index
- Short positions on stocks being removed from index
- Exact Zerodha transaction cost modeling (CNC and MIS)
- Exhaustive parameter optimization (>1M combinations)
- Historical backtesting from 2015-2025
- Dixon Technologies (DIXON.NS) specific tracking
- Walk-forward validation framework

**Performance Target:**
- Annualized return > Nifty 50 buy-and-hold
- Sharpe ratio > 1.5
- Max drawdown < 20%
- Win rate > 60%

**Usage:**
```bash
# Run full optimization (10,000+ iterations)
python strategies/index_rebalance_frontrun.py

# Results saved to:
# - backtests/index_rebalance_results.csv
# - backtests/index_rebalance_report.txt
```

**Live Trading:**
Requires Zerodha Kite Connect API. See `utils/zerodha_integration.py` and `docs/INDEX_REBALANCE_STRATEGY_GUIDE.md` for setup.

**Documentation:**
Complete implementation guide: `docs/INDEX_REBALANCE_STRATEGY_GUIDE.md`

---

All strategies are written with optimized, margin-safe, trailing stop-loss framework for live trading on Indian markets.

