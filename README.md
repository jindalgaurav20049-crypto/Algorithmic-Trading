# Algorithmic Trading for Indian Markets 🇮🇳

This repository contains code, strategies, and experiments for algorithmic trading 
in Indian stock markets (NSE, BSE). 

## 🌟 Featured Strategy: Index Rebalancing Front-Run

**NEW:** Advanced quantitative strategy targeting Nifty 50 semi-annual rebalances with >1M parameter optimizations.

**Key Features:**
- Anticipates passive fund flows during index rebalances
- Exact Zerodha transaction cost modeling (CNC/MIS)
- Historical backtesting 2015-2025 (19 rebalances)
- Dixon Technologies (DIXON.NS) specific tracking
- Live trading ready with Kite Connect integration
- Target: Outperform Nifty 50 buy-and-hold by 5-8% annualized

📖 **[Complete Guide](docs/INDEX_REBALANCE_STRATEGY_GUIDE.md)** | 📊 **[Executive Summary](docs/EXECUTIVE_SUMMARY.md)**

```bash
# Run backtest
python strategies/index_rebalance_frontrun.py
```

## Structure
- `data/` : Market data (raw & processed)
- `notebooks/` : Jupyter notebooks for research
- `strategies/` : Strategy scripts (SMA, MACD, ATR, **Index Rebalance**)
- `backtests/` : Backtest results & reports
- `configs/` : Configurations (symbols, broker settings)
- `utils/` : Helper functions & Zerodha integration
- `docs/` : Strategy guides & documentation
