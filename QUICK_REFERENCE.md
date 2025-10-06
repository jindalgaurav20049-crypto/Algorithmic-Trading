# Quick Reference Guide

## 🚀 Getting Started in 5 Minutes

### 1. Install & Test
```bash
git clone https://github.com/jindalgaurav20049-crypto/Algorithmic-Trading.git
cd Algorithmic-Trading
pip install -r requirements.txt
cd strategies
python test_system.py
```

### 2. Run Example
```bash
python example_workflow.py
```

### 3. Run Backtest
```bash
python comprehensive_sma_backtest.py
```

---

## 📁 Key Files

| File | Purpose | Size |
|------|---------|------|
| `strategies/comprehensive_sma_backtest.py` | Main backtesting script | 14KB |
| `strategies/advanced_sma_crossover.py` | Strategy implementation | 6KB |
| `utils/zerodha_charges.py` | Transaction cost calculator | 5KB |
| `utils/optimizer.py` | Parameter optimization | 11KB |
| `utils/kite_integration.py` | Live trading (Kite API) | 18KB |
| `STRATEGY_README.md` | Complete strategy guide | 12KB |
| `DELIVERY_SUMMARY.md` | What was delivered | 14KB |

---

## 💡 Common Tasks

### Calculate Transaction Costs
```python
from utils.zerodha_charges import ZerodhaCharges

# MIS (Intraday)
charges = ZerodhaCharges.calculate_mis_charges(50000, 50000)
print(f"Total: ₹{charges['total']:.2f}")

# CNC (Delivery)
charges = ZerodhaCharges.calculate_cnc_charges(50000, 50000)
print(f"Total: ₹{charges['total']:.2f}")
```

### Fetch Data
```python
from utils.data_fetcher import IntradayDataFetcher

fetcher = IntradayDataFetcher('NIFTYBEES.NS', '2024-01-01', '2024-10-06')
data = fetcher.fetch_intraday_data(interval='5m')
```

### Run Backtest
```python
from backtesting import Backtest
from strategies.advanced_sma_crossover import AdvancedSMACrossover

AdvancedSMACrossover.short_sma = 10
AdvancedSMACrossover.long_sma = 50
AdvancedSMACrossover.stop_loss = 0.05
AdvancedSMACrossover.trade_mode = 'MIS'

bt = Backtest(data, AdvancedSMACrossover, cash=100000, commission=0.001)
stats = bt.run()
print(stats)
```

### Optimize Parameters
```python
from utils.optimizer import ParameterOptimizer

optimizer = ParameterOptimizer(data, AdvancedSMACrossover)

param_grid = {
    'short_sma': range(5, 51, 5),
    'long_sma': range(20, 201, 10),
    'stop_loss': [0.03, 0.05, 0.07],
    'trade_mode': ['MIS', 'CNC']
}

results = optimizer.grid_search(param_grid, max_combinations=1000)
print(results.head())
```

### Live Trading Setup
```python
from utils.kite_integration import KiteConnectTrader, LiveSMAStrategy

# Initialize
trader = KiteConnectTrader('api_key', 'access_token')

# Create strategy
strategy = LiveSMAStrategy(
    kite_trader=trader,
    symbol='NIFTYBEES.NS',
    short_sma=10,
    long_sma=50,
    stop_loss=0.05,
    trade_mode='MIS'
)

# Run (checks every 5 minutes)
strategy.run(check_interval=300)
```

---

## 🔧 Configuration

### Parameter Ranges (in comprehensive_sma_backtest.py)

```python
# Modify these for different optimization scopes:

TIMEFRAMES = ['5m']  # ['1m', '3m', '5m', '15m']
SHORT_SMA_RANGE = range(3, 51, 2)     # 3 to 50
LONG_SMA_RANGE = range(20, 201, 5)    # 20 to 200
STOP_LOSS_RANGE = np.arange(0.0, 0.16, 0.01)  # 0% to 15%
TAKE_PROFIT_RANGE = np.arange(0.0, 0.26, 0.02)  # 0% to 25%
TRADE_MODES = ['MIS', 'CNC']
ENTRY_WINDOWS = [0, 5, 10, 15, 20, 25, 30]  # minutes
POSITION_SIZES = np.arange(0.005, 0.021, 0.0025)  # 0.5% to 2%
```

### Symbols to Test

```python
SYMBOLS = ['NIFTYBEES.NS', 'DIXON.NS', 'RELIANCE.NS', 'INFY.NS']
```

---

## 📊 Understanding Results

### Backtest Output
```
Annualized Return: 18.5%    ← Target to maximize
Sharpe Ratio: 1.85          ← Risk-adjusted return (>1 is good)
Max Drawdown: -12.3%        ← Largest loss from peak (lower is better)
Win Rate: 58%               ← % of profitable trades
Trades/Year: 145            ← Should be <200 for live trading
```

### Comparing to Buy-and-Hold
```
Strategy Return: 18.5%
Buy-Hold Return: 12.3%
Excess Return: +6.2%        ← Strategy must beat this!
```

---

## ⚠️ Important Notes

### Data Limitations
- **yfinance**: Only ~60 days of intraday data
- **Solution**: Use Kite Connect API for full historical data
- **Current**: Falls back to simulated data (disclosed in outputs)

### Before Live Trading
1. ✅ Get real historical data
2. ✅ Run full optimization (>10k combinations)
3. ✅ Walk-forward validation
4. ✅ Paper trade 1-3 months
5. ✅ Start with small capital (₹10k-50k)

### Risk Management
- Never risk >1-2% per trade
- Always use stop-losses
- Maximum 200 trades/year
- Filter for liquidity (>50k shares/day)

---

## 🆘 Troubleshooting

### "No intraday data available"
**Cause**: yfinance limitation  
**Solution**: Use Kite API or simulated data (disclosed in output)

### "No strategies outperform buy-and-hold"
**Cause**: Parameters not optimal or market conditions  
**Solution**: Try different parameter ranges or time periods

### "Kite Connect authentication failed"
**Cause**: Invalid API key/token  
**Solution**: Regenerate token (expires daily at 7:30 AM IST)

### Strategy shows 0 trades
**Cause**: No crossovers in data (common with simulated data)  
**Solution**: Use real data or adjust SMA periods

---

## 📞 Support

- **Documentation**: See STRATEGY_README.md
- **Implementation**: See IMPLEMENTATION_NOTES.md  
- **Delivery Details**: See DELIVERY_SUMMARY.md
- **Issues**: Open issue on GitHub

---

## 📈 Performance Expectations

### Conservative (Realistic)
- Return: 8-12% above risk-free
- Sharpe: 1.0-1.5
- Drawdown: 10-15%

### Moderate (Achievable)
- Return: 12-18% above risk-free
- Sharpe: 1.5-2.0
- Drawdown: 8-12%

### Optimistic (Best Case)
- Return: 18-25% above risk-free
- Sharpe: 2.0+
- Drawdown: <8%

**Note**: These are targets. Actual results will vary based on market conditions, parameters, and execution quality.

---

## 🔐 Security Checklist

- [ ] Never commit API keys to Git
- [ ] Use environment variables for credentials
- [ ] Enable 2FA on Zerodha account
- [ ] Review API logs regularly
- [ ] Limit API permissions to necessary only
- [ ] Use different keys for testing vs production

---

## ✅ Pre-Production Checklist

- [ ] Real historical data obtained
- [ ] Full optimization completed (>10k combos)
- [ ] Walk-forward validation done
- [ ] Top parameters tested across regimes
- [ ] Paper trading for 1+ months
- [ ] Monitoring and alerts configured
- [ ] Risk limits set and tested
- [ ] Backup/recovery plan in place
- [ ] Small capital for initial live test
- [ ] Legal/tax consultation done

---

**Quick Start**: `python test_system.py`  
**Full Guide**: See STRATEGY_README.md  
**Production**: See IMPLEMENTATION_NOTES.md  

**Happy Trading! 📈**
