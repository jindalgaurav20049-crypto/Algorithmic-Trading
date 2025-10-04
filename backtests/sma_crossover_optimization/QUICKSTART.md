# Quick Start Guide - SMA Crossover Strategy

## For Immediate Use

### Option 1: Use Pre-Optimized Parameters (Fastest)

The optimization is already complete. Use these optimal parameters:

```python
# Optimal Parameters
SHORT_SMA = 8      # days
LONG_SMA = 20      # days  
MAX_HOLDING = 60   # days
STOP_LOSS = 0.0    # disabled
TAKE_PROFIT = 0.0  # disabled

# Expected Performance (based on 10-year backtest)
# - Annualized Return: 18.71%
# - Sharpe Ratio: 1.15
# - Max Drawdown: 15.89%
# - Win Rate: 60.27%
```

### Option 2: Run Your Own Optimization

```bash
# Install dependencies
pip install backtesting yfinance pandas numpy matplotlib scipy tqdm

# Run the optimization (takes ~5-7 minutes)
cd /path/to/Algorithmic-Trading
python strategies/sma_crossover_optimization.py
```

Results will be saved to: `backtests/sma_crossover_optimization/`

## Implementation Steps

### Step 1: Review the Strategy
1. Open `backtests/sma_crossover_optimization/README.md` - Comprehensive documentation
2. Check `backtests/sma_crossover_optimization/optimization_report.txt` - Performance summary
3. View `backtests/sma_crossover_optimization/optimal_strategy_equity_curve.html` - Visual results

### Step 2: Understand the Risks
- Read the "Warnings and Risk Disclosures" section in README.md
- Strategy underperforms buy-and-hold by 8.83% but has lower drawdown
- No stop-loss means potential for large individual losses

### Step 3: Choose Implementation Method

#### A. Manual Trading
1. Calculate 8-day and 20-day SMAs daily
2. When 8-day SMA crosses above 20-day SMA → BUY
3. When 8-day SMA crosses below 20-day SMA → SELL
4. Exit after 60 days if no sell signal

#### B. Automated Trading
Use the provided code in `backtests/sma_crossover_optimization/live_trading_strategy.py`:

```python
from live_trading_strategy import LiveSMAStrategy

# Initialize
strategy = LiveSMAStrategy(
    account_size=100000,  # Your account size
    risk_per_trade=0.01   # Risk 1% per trade
)

# Get current data (replace with your data source)
# data = fetch_historical_data('NIFTY', days=365)
# current_price = get_current_price('NIFTY')

# Run strategy
# strategy.run(data, current_price, symbol='NIFTY')
```

#### C. Broker Integration

**For Zerodha (India):**
```python
from kiteconnect import KiteConnect

kite = KiteConnect(api_key="your_api_key")
# Set access token after login
kite.set_access_token("your_access_token")

# Place order
kite.place_order(
    tradingsymbol="NIFTY",
    exchange="NSE",
    transaction_type="BUY",  # or "SELL"
    quantity=shares,
    order_type="LIMIT",
    price=price,
    product="CNC"
)
```

**For Interactive Brokers (Global):**
```python
from ib_insync import IB, Stock, LimitOrder

ib = IB()
ib.connect('127.0.0.1', 7497, clientId=1)

contract = Stock('NIFTY', 'NSE', 'INR')
order = LimitOrder('BUY', shares, price)
trade = ib.placeOrder(contract, order)
```

**For Alpaca (US):**
```python
import alpaca_trade_api as tradeapi

api = tradeapi.REST(
    'your_api_key',
    'your_api_secret',
    'https://paper-api.alpaca.markets'
)

api.submit_order(
    symbol='SPY',  # Use SPY for S&P 500
    qty=shares,
    side='buy',  # or 'sell'
    type='limit',
    limit_price=price,
    time_in_force='day'
)
```

### Step 4: Set Up Monitoring

Create a daily checklist:
- [ ] Download latest price data
- [ ] Calculate 8-day and 20-day SMAs
- [ ] Check for crossover signals
- [ ] Execute trades if signals present
- [ ] Update position tracking
- [ ] Record trade in log

### Step 5: Position Sizing

Use one of these methods:

**Simple Fixed Percentage (Recommended for Beginners):**
```python
position_size = account_size * 0.10  # 10% per position
shares = position_size / current_price
```

**Risk-Based Sizing:**
```python
# Since no stop-loss, use volatility as proxy
account_risk = account_size * 0.01  # Risk 1%
volatility_estimate = 0.02  # 2% daily volatility
position_size = account_risk / volatility_estimate
shares = position_size / current_price
```

**Kelly Criterion (Advanced):**
```python
# Kelly suggests 40.5% but use fractional
kelly_fraction = 0.4046 * 0.25  # 25% of Kelly
position_size = account_size * kelly_fraction
shares = position_size / current_price
```

## Performance Expectations

### Monthly Performance
- Average trades per month: 0.6 (about 1 trade every 1-2 months)
- Expected monthly return: ~1.4% (compounded)
- Typical drawdown: 3-4%

### Annual Performance
- Expected annual return: 18.71%
- Expected trades per year: ~7
- Maximum drawdown: ~16%
- Win rate: 60%

### 10-Year Performance
- Starting capital: $100,000
- Expected ending capital: $555,689
- Total return: 455.69%

## Common Questions

**Q: Why does this underperform buy-and-hold?**
A: Due to transaction costs and missing some upside during trend changes. The benefit is significantly lower drawdown (15.89% vs potentially 30-40% for buy-and-hold).

**Q: Can I add a stop-loss?**
A: Yes, but the optimization found that no stop-loss performs best. If you add one, expect lower returns but faster loss cutting.

**Q: What if I trade more frequently?**
A: More frequent trading (lower SMA periods) increases costs and typically reduces returns.

**Q: Is this suitable for stocks?**
A: The strategy was optimized for indices. Individual stocks may require different parameters due to higher volatility.

**Q: What account size do I need?**
A: Minimum $10,000, recommended $50,000+. Smaller accounts suffer disproportionately from transaction costs.

**Q: How do I know when to stop using the strategy?**
A: Consider stopping if:
- Sharpe ratio falls below 0.5 for 12 months
- Maximum drawdown exceeds 25%
- Win rate falls below 45% for 20 trades
- Strategy shows consistent underperformance for 2 years

## Checklist Before Going Live

- [ ] I understand the strategy completely
- [ ] I've read all risk disclosures
- [ ] I've tested the code on historical data
- [ ] I have sufficient capital ($10,000+ minimum)
- [ ] I understand position sizing
- [ ] I have a broker account set up
- [ ] I've configured API access (if automated)
- [ ] I've set up trade logging
- [ ] I have a plan for monitoring performance
- [ ] I'm comfortable with the maximum drawdown (15.89%)
- [ ] I understand this underperforms buy-and-hold
- [ ] I'm using this for lower volatility, not maximum returns

## Next Steps

1. **Paper Trade First**: Test for 3-6 months with paper money
2. **Start Small**: Begin with 10-25% of planned capital
3. **Monitor Closely**: Review daily for first month
4. **Scale Gradually**: Increase position size as confidence grows
5. **Keep Records**: Log every trade and monthly performance
6. **Review Quarterly**: Assess if strategy still meets goals

## Support Files

| File | Purpose |
|------|---------|
| `README.md` | Comprehensive documentation |
| `optimization_report.txt` | Performance summary |
| `optimization_results.json` | Raw optimization data |
| `live_trading_strategy.py` | Production code |
| `trade_log.csv` | Historical trades |
| `optimal_strategy_equity_curve.html` | Visual results |

## Emergency Contacts

If strategy performance degrades:
1. Check for data quality issues
2. Verify parameter settings
3. Review market regime (unusual volatility?)
4. Consider pausing trading
5. Re-optimize with recent data

## Legal Disclaimer

**This is for educational purposes only. Not financial advice.**

- Past performance ≠ future results
- Trading involves risk of loss
- Only invest capital you can afford to lose
- Consult a financial advisor before trading
- The authors assume no liability for trading losses

---

**Ready to Start?**

1. Review README.md thoroughly
2. Run optimization or use pre-optimized parameters
3. Paper trade for 3-6 months
4. Go live with small position sizes
5. Scale up gradually based on results

Good luck, and trade responsibly! 🚀📈
