# 🚀 PocketOption Trading Automation Tool

A comprehensive trading automation system for PocketOption binary options platform, featuring 3 advanced martingale strategies with precise timing optimization and comprehensive analytics.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Trading Strategies](#trading-strategies)
- [CLI Commands](#cli-commands)
- [Configuration](#configuration)
- [Safety Features](#safety-features)
- [Technical Architecture](#technical-architecture)

## ✨ Features

### 🎯 Three Main Trading Strategies
1. **3-Cycle Cumulative Martingale** - Aggressive automated strategy
2. **2-Cycle Reset Martingale** - Moderate automated strategy  
3. **Manual 2-Cycle Martingale** - Conservative user-controlled strategy

### 🔧 Advanced Technical Features
- **Precise Timing System** - 8-second advance execution with optimization
- **Asset Availability Filtering** - Only trades verified available assets
- **Comprehensive Analytics** - Detailed performance tracking and metrics
- **Safety Controls** - Stop loss, take profit, and balance protection
- **Demo/Real Account Support** - Safe testing with demo accounts
- **Connection Management** - Automatic retry logic and session handling

## 🚀 Installation

### Prerequisites
- Python 3.8+
- PocketOption account
- Valid SSID from browser DevTools

### Setup Steps

1. **Clone and Setup Environment**
```bash
git clone <repository>
cd PocketOptionAPI
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**
```bash
cp .env.example .env
# Edit .env file with your SSID
```

3. **Get SSID from Browser**
- Open PocketOption in browser and login
- Press F12 → Network tab → Filter by "WS"
- Look for message starting with `42["auth",{...}]`
- Copy complete message to .env file

## 🎮 Quick Start

### Interactive Mode
```bash
python pocketoption_app.py
```

### CLI Commands
```bash
# Test connection
python pocketoption_app.py --test-connection

# Check balance
python pocketoption_app.py --get-balance --account demo

# Verbose mode
python pocketoption_app.py --verbose
```

## 📊 Trading Strategies

### 1. 🤖 Automated 3-Cycle Cumulative Martingale

**Best For:** Experienced traders seeking maximum profit potential
**Risk Level:** High
**Automation:** Fully automated using CSV signals

#### How It Works:
- **Cycle 1:** Base → Base×Multiplier → Base×Multiplier²
- **Cycle 2:** Continues from Cycle 1 final amount
- **Cycle 3:** Enhanced progression from Cycle 2
- **Reset:** After 3 complete cycles or on any win

#### Input Requirements:
```
Account Type: demo/real
Base Amount: $1.00 (minimum)
Multiplier: 2.5 (recommended)
Stop Loss: $100 (optional)
Take Profit: $50 (optional)
```

#### Example Progression:
```
Signal: EURGBP PUT
Cycle 1: $1.00 → $2.50 → $6.25
Cycle 2: $15.63 → $39.08 → $97.70
Cycle 3: $244.25 → $610.63 → $1,526.58
```

### 2. 🎯 Automated 2-Cycle Reset Martingale

**Best For:** Balanced risk/reward approach
**Risk Level:** Moderate
**Automation:** Fully automated using CSV signals

#### How It Works:
- **Cycle 1:** Base → Base×Multiplier
- **Cycle 2:** RESETS to Base → Base×Multiplier
- **Independent Cycles:** Each cycle starts fresh
- **Lower Risk:** Faster recovery from losses

#### Input Requirements:
```
Account Type: demo/real
Base Amount: $1.00 (minimum)
Multiplier: 2.5 (recommended)
Stop Loss: $50 (optional)
Take Profit: $25 (optional)
```

#### Example Progression:
```
Signal: EURUSD CALL
Cycle 1: $1.00 → $2.50 (if loss)
Cycle 2: $1.00 → $2.50 (reset, independent)
```

### 3. 📝 Manual 2-Cycle Martingale

**Best For:** Conservative traders wanting full control
**Risk Level:** Low (user controlled)
**Automation:** Manual input for each trade

#### How It Works:
- **User Control:** Manual confirmation for each trade
- **Asset Flexibility:** Change assets between cycles
- **Direction Control:** Modify direction per cycle
- **Real-time Decisions:** Adapt strategy based on market

#### Input Requirements:
```
Account Type: demo/real
Base Amount: $1.00 (minimum)
Multiplier: 2.5 (recommended)
Asset: EURUSD (from available list)
Direction: call/put
Timeframe: 60 minutes (recommended)

Cycle 2 Configuration:
New Asset: GBPUSD (can change)
New Direction: put (can change)
```

## 🛠️ CLI Commands

### Connection & Status
```bash
# Test API connection
python pocketoption_app.py --test-connection

# Get account balance
python pocketoption_app.py --get-balance --account demo
python pocketoption_app.py --get-balance --account real

# Verbose logging
python pocketoption_app.py --verbose
```

### Utility Functions
Available in interactive mode (Option 4):
- **Test Connection** - Verify API connectivity
- **Get Balance** - Check account balance
- **List Available Assets** - Show tradeable currency pairs
- **Test Single Trade** - Place one test trade

## ⚙️ Configuration

### Environment Variables (.env)
```bash
# PocketOption SSID (Required)
SSID='42["auth",{"session":"your_session_token","isDemo":1,"uid":12345,"platform":1}]'

# Telegram API (Optional - for signal monitoring)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
```

### Available Trading Assets
```
Major Pairs: EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD
Cross Pairs: EURGBP, AUDUSD, NZDUSD, AUDCAD, AUDCHF
Additional: AUDJPY, CADCHF, CADJPY, CHFJPY, EURCHF
Extended: EURJPY, EURNZD, GBPAUD, GBPJPY, NZDJPY
```

### CSV Signal Format
```csv
timestamp,asset,direction,signal_time,message_text
2026-01-03 14:31:19,EURGBP,put,14:46,📊 EURGBP-OTCp ⏰ 14:46...
```

## 🛡️ Safety Features

### Account Protection
- **Demo Account Default** - Always defaults to safe demo trading
- **Balance Verification** - Checks sufficient funds before trades
- **Asset Validation** - Only trades verified available assets
- **Input Validation** - Validates all user inputs

### Risk Management
- **Stop Loss Protection** - Automatic session termination on loss limit
- **Take Profit Targets** - Automatic session termination on profit target
- **Position Sizing** - Controlled trade amounts with multiplier limits
- **Connection Monitoring** - Automatic reconnection on failures

### User Controls
- **Confirmation Required** - User must confirm before real money trades
- **Manual Override** - Can stop trading at any time
- **Transparent Reporting** - Real-time P&L and performance metrics
- **Error Handling** - Graceful error recovery and reporting

## 🏗️ Technical Architecture

### Core Components

#### 1. PocketOptionTrader Class
```python
# Main trading engine with:
- Connection management with retry logic
- Asset availability filtering
- Trade execution with timing optimization
- Result verification and P&L calculation
- Session statistics and performance tracking
```

#### 2. MartingaleStrategy Class
```python
# Strategy implementation with:
- Cumulative and reset progression logic
- Stop loss and take profit management
- Cycle and step tracking
- Amount calculation algorithms
```

#### 3. Timing System
```python
@dataclass
class TradeTimingInfo:
    signal_time: str
    execution_start: float
    execution_end: float
    trade_placed: float
    result_checked: float
    total_duration: float
    success: bool

@dataclass
class ExecutionTimingTracker:
    avg_execution_time: float = 8.0
    measurements: List[float]
    
    def add_measurement(self, duration: float):
        # Learns from execution times for optimization
```

#### 4. Session Management
```python
@dataclass
class SessionTimingInfo:
    start_time: datetime
    total_trades: int = 0
    successful_trades: int = 0
    failed_trades: int = 0
    total_profit: float = 0.0
```

### Data Flow
```
1. Load Signals (CSV) → Filter Available Assets
2. Initialize Strategy → Connect to API
3. Execute Trades → Monitor Results
4. Update Strategy → Check Stop Conditions
5. Generate Reports → Disconnect
```

### Performance Optimization
- **Timing Compensation** - 8-second advance execution
- **Execution Learning** - Adapts timing based on measured performance
- **Parallel Processing** - Multiple signals processed efficiently
- **Connection Pooling** - Maintains persistent API connections
- **Memory Management** - Efficient data structures and cleanup

## 📈 Performance Metrics

### Real-time Tracking
- **Win Rate** - Percentage of successful trades
- **Total P&L** - Session profit/loss in dollars
- **Execution Time** - Average trade placement speed
- **Success Rate** - Trade execution success percentage

### Session Analytics
- **Trade Count** - Total number of trades executed
- **Cycle Performance** - Success rate by martingale cycle
- **Asset Performance** - P&L breakdown by trading pair
- **Timing Analysis** - Execution speed optimization data

## 🔧 Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Test connection
python pocketoption_app.py --test-connection

# Check SSID format
# Should start with: 42["auth",{...}]
```

#### Invalid Assets
```bash
# List available assets
python pocketoption_app.py
# Select Option 4 → Option 3
```

#### SSID Expiration
- Get fresh SSID from browser DevTools
- Update .env file with new SSID
- Restart application

### Error Messages
- **"Invalid asset"** - Asset not available for trading
- **"Connection failed"** - Check SSID and internet connection
- **"Insufficient balance"** - Reduce trade amount or add funds
- **"Authentication failed"** - Get fresh SSID from browser

## 📞 Support

### Getting Help
1. Check this README for common solutions
2. Verify SSID is fresh and correctly formatted
3. Test with demo account first
4. Use verbose mode for detailed logging

### Best Practices
- **Always test with demo account first**
- **Start with small amounts**
- **Use stop loss protection**
- **Monitor performance metrics**
- **Keep SSID updated**

---

## ⚠️ Disclaimer

This software is for educational purposes only. Binary options trading involves significant risk and may not be suitable for all investors. Past performance does not guarantee future results. Always trade responsibly and never risk more than you can afford to lose.

**Use demo accounts for testing and learning before risking real money.**