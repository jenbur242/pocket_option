# $1 CALL Trading Guide for PocketOption

## Overview
Simple trading setup that uses exactly **$1 per trade** for CALL (Buy/Up) operations on PocketOption.

## Files Created

### 1. `setup_1dollar_call_trades.py` - Main Trading Script
- **Purpose**: Interactive $1 CALL trader
- **Features**:
  - Fixed $1 per trade
  - CALL direction only (Buy/Up)
  - 8 recommended major currency pairs
  - Single or batch trading
  - Real-time execution

### 2. `simple_1dollar_trader.py` - Alternative Interface  
- **Purpose**: Alternative trading interface
- **Features**:
  - Same $1 trading functionality
  - Different menu system
  - Quick trade options

### 3. `test_1dollar_setup.py` - Testing Script
- **Purpose**: Test setup without real trades
- **Features**:
  - Verify asset availability
  - Test configuration
  - No actual money spent

## Available Assets (8 Major Pairs)

| Asset | Description | Asset ID |
|-------|-------------|----------|
| EURUSD | Euro/US Dollar | 70 |
| GBPUSD | British Pound/US Dollar | 75 |
| USDJPY | US Dollar/Japanese Yen | 78 |
| AUDUSD | Australian Dollar/US Dollar | 61 |
| USDCAD | US Dollar/Canadian Dollar | 76 |
| EURGBP | Euro/British Pound | 68 |
| EURJPY | Euro/Japanese Yen | 69 |
| GBPJPY | British Pound/Japanese Yen | 74 |

## How to Use

### Prerequisites
1. **Environment Setup**: Add to `.env` file:
   ```
   POCKETOPTION_EMAIL=your_email@example.com
   POCKETOPTION_PASSWORD=your_password
   ```

2. **Account Balance**: Ensure you have at least $1 in your PocketOption account

### Quick Start

#### Option 1: Interactive Trading
```bash
python setup_1dollar_call_trades.py
```

**Menu Options**:
- `1` - Single CALL trade (choose asset)
- `2` - Multiple CALL trades (batch)
- `3` - Show available assets
- `4` - Quick EURUSD trade
- `5` - Exit

#### Option 2: Test First (Recommended)
```bash
python test_1dollar_setup.py
```
This verifies everything works without spending money.

### Trading Examples

#### Single Trade Example
1. Run the script
2. Select option `1` (Single CALL trade)
3. Choose asset (e.g., `1` for EURUSD)
4. Set duration (default: 1 minute)
5. Confirm execution

**Result**: $1 CALL trade on EURUSD for 1 minute

#### Batch Trade Example  
1. Run the script
2. Select option `2` (Multiple CALL trades)
3. Choose assets (e.g., `1,2,3` for first 3 assets)
4. Set duration (default: 1 minute)
5. Confirm batch execution

**Result**: $3 total investment ($1 each on 3 assets)

#### Quick Trade Example
1. Run the script
2. Select option `4` (Quick EURUSD trade)

**Result**: Instant $1 CALL trade on EURUSD

## Trade Configuration

### Fixed Settings
- **Amount**: $1.00 (cannot be changed)
- **Direction**: CALL (Buy/Up only)
- **Trade Type**: Binary Options

### Configurable Settings
- **Asset**: Choose from 8 available pairs
- **Duration**: 1-5 minutes (default: 1 minute)
- **Quantity**: Single or multiple trades

## Expected Returns
- **Successful Trade**: ~80-85% return ($1.80-$1.85 total)
- **Failed Trade**: $0 (lose the $1 investment)
- **Break-even**: Need ~54% win rate to be profitable

## Risk Management

### Built-in Safety Features
1. **Fixed Amount**: Cannot accidentally trade more than $1
2. **CALL Only**: Simplified to one direction
3. **Major Pairs**: High liquidity, lower risk
4. **Confirmation**: Always asks before executing

### Recommendations
- Start with single trades to test
- Use 1-minute duration for quick results
- Focus on major pairs (EURUSD, GBPUSD, USDJPY)
- Don't risk more than you can afford to lose

## Troubleshooting

### Common Issues

#### "Missing credentials in .env file"
**Solution**: Add your PocketOption email and password to `.env` file

#### "Asset not available"
**Solution**: Use `test_1dollar_setup.py` to check which assets are available

#### "Connection failed"
**Solution**: 
- Check internet connection
- Verify PocketOption credentials
- Try different server region

#### "Insufficient balance"
**Solution**: Deposit at least $1 to your PocketOption account

### Getting Help
1. Run `test_1dollar_setup.py` first
2. Check console output for specific error messages
3. Verify `.env` file has correct credentials
4. Ensure PocketOption account has sufficient balance

## Files Summary

| File | Purpose | Safe to Run |
|------|---------|-------------|
| `setup_1dollar_call_trades.py` | Main trader | ⚠️ Uses real money |
| `simple_1dollar_trader.py` | Alternative interface | ⚠️ Uses real money |
| `test_1dollar_setup.py` | Testing only | ✅ No money spent |
| `1DOLLAR_TRADING_GUIDE.md` | This guide | ✅ Documentation |

## Next Steps
1. **Test First**: Run `test_1dollar_setup.py`
2. **Start Small**: Begin with single trades
3. **Learn Patterns**: Observe which assets perform better
4. **Scale Gradually**: Use batch trades once comfortable

---

**⚠️ Risk Warning**: Binary options trading involves significant risk. Only trade with money you can afford to lose. This tool is for educational purposes.