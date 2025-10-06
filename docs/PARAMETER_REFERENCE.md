# Parameter Reference Guide - Index Rebalancing Strategy

## Quick Reference for Strategy Parameters

This guide provides a detailed explanation of each parameter used in the Index Rebalancing Front-Running strategy.

---

## 📊 Optimization Parameters

### 1. Entry Timing (`entry_days_post_announcement`)

**Definition:** Number of trading days after NSE announcement to enter positions

**Range:** 0-10 days  
**Optimal (typical):** 2-3 days

**Rationale:**
- Day 0-1: Immediate reaction, high volatility, poor execution
- Day 2-3: **Sweet spot** - retail awareness building, before institutional bulk
- Day 4+: Most price impact already occurred

**Trade-off:**
- Earlier entry → Higher risk, better average price
- Later entry → Lower risk, missed some move

**Example:**
```python
announcement_date = '2025-01-31'
entry_days = 2
entry_date = '2025-02-02'  # 2 trading days later
```

---

### 2. Exit Timing (`exit_days_post_effective`)

**Definition:** Number of trading days after effective date to exit positions

**Range:** 0-10 days  
**Optimal (typical):** 3-5 days

**Rationale:**
- Day 0: Effective date - maximum fund rebalancing activity
- Day 1-3: Continued flow as funds complete rebalancing
- Day 4-7: Flow subsiding, price reverting
- Day 8+: Price fully reverted, no edge remaining

**Trade-off:**
- Earlier exit → Lock in gains, miss potential upside
- Later exit → Risk mean reversion, higher returns if sustained

**Example:**
```python
effective_date = '2025-03-31'
exit_days = 3
exit_date = '2025-04-03'  # 3 trading days after effective
```

---

### 3. Position Size (`position_size_pct`)

**Definition:** Percentage of total capital allocated per stock

**Range:** 0.5% - 5.0%  
**Optimal (typical):** 2.0-3.0%

**Rationale:**
- 0.5-1%: Conservative, limited impact even if all trades win
- 2-3%: **Balanced** - significant exposure, manageable risk
- 4-5%: Aggressive, high concentration risk

**Calculation:**
```python
capital = 1,000,000  # ₹10 lakh
position_size_pct = 2.5
stock_price = 5000

position_value = capital * (position_size_pct / 100)  # ₹25,000
quantity = int(position_value / stock_price)  # 5 shares
```

**Diversification:**
- Typical rebalance: 2-4 stocks changed
- Max exposure: 2.5% × 4 = 10% of capital per event
- Annual: ~2 events → 20% total capital deployed/year

---

### 4. Stop-Loss (`stop_loss_pct`)

**Definition:** Maximum loss percentage before auto-exit

**Range:** 0% - 10%  
**Optimal (typical):** 4-6%

**Rationale:**
- 0%: No stop → Unlimited loss risk
- 2-3%: Too tight → Stopped out by normal volatility
- 4-6%: **Optimal** - Protects against major adverse moves
- 8-10%: Too wide → Large losses if thesis wrong

**Example:**
```python
entry_price = 5000
stop_loss_pct = 5.0

# For LONG position
stop_loss_price = entry_price * (1 - stop_loss_pct/100)  # ₹4,750

# For SHORT position
stop_loss_price = entry_price * (1 + stop_loss_pct/100)  # ₹5,250
```

**Zerodha Implementation:**
```python
# Stop-loss order automatically placed after entry
order_manager.place_stop_loss_order(
    symbol='DIXON',
    quantity=5,
    trigger_price=4800,  # Stop triggers here
    price=4750,          # Order placed at this price
    transaction_type='SELL'
)
```

---

### 5. Take-Profit (`take_profit_pct`)

**Definition:** Target profit percentage for auto-exit

**Range:** 0% - 15%  
**Optimal (typical):** 8-12%

**Rationale:**
- 0%: No target → Hold until exit date (time-based)
- 3-5%: Conservative - frequent exits, limited gains
- 8-12%: **Optimal** - Captures most rebalancing impact
- 13-15%: Ambitious - rarely hit, most positions held longer

**Example:**
```python
entry_price = 5000
take_profit_pct = 10.0

# For LONG position
take_profit_price = entry_price * (1 + take_profit_pct/100)  # ₹5,500

# For SHORT position
take_profit_price = entry_price * (1 - take_profit_pct/100)  # ₹4,500
```

**Logic:**
- Check daily if current price exceeds target
- If hit, close position immediately
- Otherwise, hold until scheduled exit date

---

### 6. Flow Filter (`flow_filter_cr`)

**Definition:** Minimum estimated fund flow (in ₹ crores) to execute trade

**Range:** ₹100 - ₹1000 crores  
**Optimal (typical):** ₹400-600 crores

**Rationale:**
- Small flows (<₹200cr): Minimal price impact, not worth trading costs
- Medium flows (₹400-600cr): **Optimal** - Sufficient impact, good risk/reward
- Large flows (>₹800cr): Strong impact but rare events

**Estimation:**
```python
# Based on passive Nifty 50 AUM (~₹50,000+ crores)
# Stock weight in index: 2%
# Passive tracking: 60% of total AUM

estimated_flow_cr = 50000 * 0.02 * 0.60  # ₹600 crores
```

**Decision:**
```python
if estimated_flow < flow_filter_cr:
    print(f"Skip trade - flow {estimated_flow} below threshold")
    return  # Don't trade
```

---

### 7. Trade Mode (`trade_mode`)

**Definition:** Zerodha order execution mode

**Options:** 'CNC' (delivery) or 'MIS' (intraday)  
**Optimal:** 'CNC' for longs, 'MIS' for shorts

**CNC (Cash and Carry / Delivery):**
- **Use for:** LONG positions (additions)
- **Holding:** Overnight, multi-day
- **Margin:** Full payment required
- **Brokerage:** ₹0
- **DP Charges:** ₹15.34 on sell
- **Suitable:** Multi-day rebalancing strategy

**MIS (Margin Intraday Square-off):**
- **Use for:** SHORT positions (removals)
- **Holding:** Intraday only (auto-squareoff 3:20 PM)
- **Margin:** 5x leverage typical
- **Brokerage:** ₹20 or 0.03%
- **Suitable:** Short selling (easier than CNC shorts)

**Example:**
```python
# Long position (stock being added)
order_manager.place_long_order(
    symbol='DIXON',
    quantity=5,
    price=5000,
    product='CNC'  # Delivery
)

# Short position (stock being removed)
order_manager.place_short_order(
    symbol='OLDSTOCK',
    quantity=10,
    price=1000,
    product='MIS'  # Intraday
)
```

**Note on Shorts:**
- MIS shorts auto-squareoff at 3:20 PM IST
- For multi-day shorts, need SBL (Securities Borrowing and Lending)
- Strategy typically uses MIS for simplicity

---

## 🎯 Parameter Combinations

### Total Combinations
```
11 (entry_days) × 
11 (exit_days) × 
10 (position_size) × 
21 (stop_loss) × 
16 (take_profit) × 
10 (flow_filter) × 
2 (trade_mode) = 8,131,200 combinations
```

### Optimization Strategy

**Stage 1: Grid Search (Random Sampling)**
- Sample 10,000-50,000 combinations
- Test across all historical rebalances
- Identify top 10% performers

**Stage 2: Fine-Tuning (Optional)**
- Genetic algorithm on top performers
- Test parameter sensitivity
- Validate on out-of-sample data

**Stage 3: Walk-Forward Validation**
- 7 years in-sample (2015-2022): Find best params
- 3 years out-of-sample (2022-2025): Validate
- Rolling: Update params every 2 rebalance cycles

---

## 📈 Optimal Parameter Sets (Examples)

### Conservative Profile
```python
params = {
    'entry_days_post_announcement': 3,    # Wait for volatility to settle
    'exit_days_post_effective': 2,        # Exit early, lock gains
    'position_size_pct': 1.5,             # Small positions
    'stop_loss_pct': 4.0,                 # Tight stop
    'take_profit_pct': 8.0,               # Modest target
    'flow_filter_cr': 600,                # Only large flows
    'trade_mode': 'CNC'
}
# Expected: Lower return, lower risk, higher Sharpe
```

### Balanced Profile (Recommended)
```python
params = {
    'entry_days_post_announcement': 2,
    'exit_days_post_effective': 3,
    'position_size_pct': 2.5,
    'stop_loss_pct': 5.0,
    'take_profit_pct': 10.0,
    'flow_filter_cr': 500,
    'trade_mode': 'CNC'
}
# Expected: 15-20% annualized, moderate risk
```

### Aggressive Profile
```python
params = {
    'entry_days_post_announcement': 1,    # Early entry
    'exit_days_post_effective': 5,        # Hold longer
    'position_size_pct': 4.0,             # Large positions
    'stop_loss_pct': 7.0,                 # Wider stop
    'take_profit_pct': 15.0,              # Ambitious target
    'flow_filter_cr': 300,                # More trades
    'trade_mode': 'CNC'
}
# Expected: Higher return, higher risk, lower Sharpe
```

---

## 🔍 Parameter Sensitivity Analysis

### Most Important Parameters (by impact)

1. **Entry/Exit Timing** (40% impact on returns)
   - Critical for capturing price movement
   - Highly sensitive to market regime

2. **Position Size** (30% impact on returns)
   - Direct multiplier on gains/losses
   - Affects portfolio volatility

3. **Stop-Loss** (20% impact on risk-adjusted returns)
   - Protects against adverse moves
   - Too tight → frequent stops, lower returns
   - Too wide → large losses

4. **Flow Filter** (10% impact on trade frequency)
   - Filters out low-impact events
   - Improves win rate, reduces noise trades

### Robust Parameter Ranges

Parameters that work across different market regimes:

- **Entry:** 1-3 days (flexible, not too early/late)
- **Exit:** 2-5 days (captures most flow)
- **Position:** 2-3% (balanced risk/return)
- **Stop-Loss:** 4-6% (allows volatility, limits loss)
- **Take-Profit:** 8-12% (realistic target)

---

## 🧮 Parameter Interaction Effects

### Entry × Exit
```
Early Entry + Early Exit → Conservative, lower return
Early Entry + Late Exit → Aggressive, higher volatility
Late Entry + Early Exit → Ultra-conservative, minimal exposure
Late Entry + Late Exit → Miss most move, poor returns
```

### Position Size × Stop-Loss
```
Large Position + Tight Stop → High turnover, choppy
Large Position + Wide Stop → High risk, potential large loss
Small Position + Tight Stop → Low risk, low return
Small Position + Wide Stop → Optimal for high win rate
```

---

## 💡 Tips for Parameter Selection

1. **Start Conservative**
   - Use smaller positions initially
   - Tighter stops until confident
   - Higher flow filters

2. **Validate Thoroughly**
   - Test on out-of-sample data
   - Check performance across regimes
   - Verify win rate > 55%

3. **Adapt to Market**
   - Bull market: Wider stops, larger positions
   - Bear market: Tighter stops, smaller positions
   - High volatility: Earlier exits

4. **Monitor Degradation**
   - If strategy stops working → Parameters outdated
   - Re-optimize every 12-18 months
   - Watch for crowding (win rate drops)

---

## 🚀 Quick Start Command

```python
# Run optimization with custom parameters
from strategies.index_rebalance_frontrun import ParameterOptimizer

optimizer = ParameterOptimizer(rebalance_events, initial_capital=1000000)

# Test specific parameter set
params = {
    'entry_days_post_announcement': 2,
    'exit_days_post_effective': 3,
    'position_size_pct': 2.5,
    'stop_loss_pct': 5.0,
    'take_profit_pct': 10.0,
    'flow_filter_cr': 500,
    'trade_mode': 'CNC'
}

result = optimizer.backtest_full_period(params)
print(f"Annualized Return: {result['annualized_return']:.2f}%")
```

---

*For complete strategy documentation, see: `docs/INDEX_REBALANCE_STRATEGY_GUIDE.md`*
