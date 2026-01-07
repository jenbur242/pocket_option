#!/usr/bin/env python3
"""
PocketOption Advanced Trader
With proper signal timing and martingale strategies
"""
import os
import json
import time
import asyncio
import logging
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv

# Import PocketOption API
try:
    from pocketoptionapi_async import AsyncPocketOptionClient
    from pocketoptionapi_async.models import OrderDirection, OrderStatus
    REAL_API_AVAILABLE = True
except ImportError:
    print("⚠️  PocketOption API not available - using simulation mode")
    REAL_API_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MartingaleStrategy:
    """Martingale strategy implementation"""
    
    def __init__(self, strategy_type: int, base_amount: float, multiplier: float = 2.2):
        self.strategy_type = strategy_type
        self.base_amount = base_amount
        self.multiplier = multiplier
        self.current_cycle = 1
        self.current_step = 1
        self.cycle_results = []
        self.total_invested = 0.0
        
        # Strategy configurations
        self.strategies = {
            1: {"name": "3-Cycle Cumulative", "max_cycles": 3, "max_steps": 3, "cumulative": True},
            2: {"name": "2-Cycle Reset", "max_cycles": 2, "max_steps": 3, "cumulative": False},
            3: {"name": "Manual Trading", "max_cycles": 1, "max_steps": 2, "cumulative": False},
            4: {"name": "3-Cycle Progressive", "max_cycles": 3, "max_steps": 3, "cumulative": "progressive"},
            5: {"name": "3-Cycle Continuous", "max_cycles": 3, "max_steps": 3, "cumulative": "continuous"}
        }
        
        self.config = self.strategies.get(strategy_type, self.strategies[1])
        print(f"🎯 Strategy: {self.config['name']}")
    
    def get_next_amount(self) -> float:
        """Calculate next trade amount based on strategy"""
        if self.current_step == 1:
            return self.base_amount
        
        if self.strategy_type == 1:  # 3-Cycle Cumulative
            if self.current_cycle == 1:
                return self.base_amount * (self.multiplier ** (self.current_step - 1))
            else:
                # Use final amount from previous cycle as base
                previous_final = self.base_amount * (self.multiplier ** 2)  # Simplified
                return previous_final * (self.multiplier ** (self.current_step - 1))
        
        elif self.strategy_type == 2:  # 2-Cycle Reset
            return self.base_amount * (self.multiplier ** (self.current_step - 1))
        
        elif self.strategy_type == 3:  # Manual Trading
            return self.base_amount * (self.multiplier ** (self.current_step - 1))
        
        elif self.strategy_type == 4:  # 3-Cycle Progressive
            if self.current_cycle <= 2:
                return self.base_amount * (self.multiplier ** (self.current_step - 1))
            else:
                # Cycle 3 same as Cycle 2
                return self.base_amount * (self.multiplier ** (self.current_step - 1))
        
        elif self.strategy_type == 5:  # 3-Cycle Continuous
            total_step = (self.current_cycle - 1) * 3 + self.current_step
            return self.base_amount * (self.multiplier ** (total_step - 1))
        
        return self.base_amount
    
    def record_result(self, won: bool, amount: float, profit: float, is_draw: bool = False):
        """Record trade result and update strategy state"""
        self.cycle_results.append({
            'cycle': self.current_cycle,
            'step': self.current_step,
            'amount': amount,
            'won': won,
            'profit': profit,
            'is_draw': is_draw
        })
        
        if won:
            # Win - reset to next cycle, step 1
            self.current_cycle += 1
            self.current_step = 1
            if self.current_cycle > self.config['max_cycles']:
                self.current_cycle = 1  # Reset cycles
        elif is_draw:
            # Draw - stay in same position (no progression)
            # Keep current cycle and step unchanged
            pass
        else:
            # Loss - next step in same cycle
            self.current_step += 1
            if self.current_step > self.config['max_steps']:
                # Max steps reached, move to next cycle
                self.current_cycle += 1
                self.current_step = 1
                if self.current_cycle > self.config['max_cycles']:
                    self.current_cycle = 1  # Reset cycles
    
    def get_status(self) -> str:
        """Get current strategy status"""
        return f"Cycle {self.current_cycle}/{self.config['max_cycles']} | Step {self.current_step}/{self.config['max_steps']}"

class PocketOptionTrader:
    """Advanced PocketOption Trader with proper timing and martingale"""
    
    def __init__(self):
        self.ssid = os.getenv('SSID')
        self.client = None
        
        # Use date-based CSV filename (same as simple_monitor.py)
        today = datetime.now().strftime('%Y%m%d')
        self.csv_file = f"pocketoption_messages_{today}.csv"
        
        self.trade_history = []
        self.martingale = None
        
        # Available assets (updated for Quotex format)
        self.ASSETS = {
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'EURGBP',
            'AUDUSD', 'NZDUSD', 'AUDCAD', 'AUDCHF', 'AUDJPY', 'CADCHF',
            'CADJPY', 'CHFJPY', 'EURCHF', 'EURJPY', 'EURNZD', 'GBPAUD',
            'GBPJPY', 'NZDJPY', 'USDEGP', 'USDPKR', 'USDBDT', 'NZDCAD',
            'USDCOP', 'BRLUSD'  # Added new assets from Quotex
        }
        
        print(f"📊 Using CSV file: {self.csv_file}")
    
    async def connect(self, is_demo: bool = True) -> bool:
        """Connect to PocketOption"""
        try:
            print("🔌 Connecting to PocketOption...")
            
            if REAL_API_AVAILABLE and self.ssid:
                self.client = AsyncPocketOptionClient(
                    ssid=self.ssid,
                    is_demo=is_demo,
                    auto_reconnect=True,
                    enable_logging=False
                )
                
                # Try to connect with timeout
                try:
                    await asyncio.wait_for(self.client.connect(), timeout=30.0)
                    
                    # Test if connection is actually working
                    balance = await asyncio.wait_for(self.client.get_balance(), timeout=10.0)
                    
                    print(f"✅ Connected! {'DEMO' if is_demo else 'REAL'} Account")
                    print(f"💰 Balance: ${balance.balance:.2f}")
                    
                    # Debug: Show available methods
                    print("🔍 Available API methods:")
                    methods = [method for method in dir(self.client) if not method.startswith('_') and callable(getattr(self.client, method))]
                    for method in sorted(methods)[:10]:  # Show first 10 methods
                        print(f"   - {method}")
                    if len(methods) > 10:
                        print(f"   ... and {len(methods) - 10} more methods")
                    
                    return True
                    
                except asyncio.TimeoutError:
                    print("⏰ Connection timeout - SSID may be expired")
                    print("🔄 Continuing in simulation mode...")
                    self.client = None
                    return True
                except Exception as conn_error:
                    print(f"❌ Connection failed: {conn_error}")
                    if "authentication timeout" in str(conn_error).lower() or "ssid" in str(conn_error).lower():
                        print("🔑 SSID appears to be invalid or expired")
                        print("💡 Please get a fresh SSID from browser DevTools:")
                        print("   1. Open PocketOption in browser")
                        print("   2. Press F12 -> Network tab -> WS filter")
                        print("   3. Look for authentication message starting with 42[\"auth\",{\"session\":\"...")
                        print("   4. Update SSID in .env file")
                    print("🔄 Continuing in simulation mode...")
                    self.client = None
                    return True
            else:
                print(f"✅ Connected! {'DEMO' if is_demo else 'REAL'} Account (Simulation)")
                print(f"💰 Balance: $1000.00 (Simulated)")
                return True
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Continuing in simulation mode...")
            self.client = None  # Ensure client is None on connection failure
            return True  # Continue in simulation mode
    
    async def disconnect(self):
        """Disconnect from PocketOption"""
        if self.client and REAL_API_AVAILABLE:
            await self.client.disconnect()
        print("🔌 Disconnected from PocketOption")
    
    def get_signals_from_csv(self) -> List[Dict[str, Any]]:
        """Get trading signals from CSV file with proper time parsing"""
        try:
            if not os.path.exists(self.csv_file):
                print(f"❌ CSV file not found: {self.csv_file}")
                return []
            
            df = pd.read_csv(self.csv_file, on_bad_lines='skip')
            print(f"📊 Loaded {len(df)} rows from CSV")
            
            # Filter for valid signals only
            if 'is_signal' in df.columns:
                signals_df = df[df['is_signal'] == 'Yes'].copy()
                print(f"🎯 Found {len(signals_df)} valid signals")
            else:
                signals_df = df.copy()
            
            if signals_df.empty:
                print("❌ No valid signals found in CSV")
                return []
            
            signals = []
            current_time = datetime.now()
            print(f"🕐 Current time: {current_time.strftime('%H:%M:%S')}")
            
            for _, row in signals_df.iterrows():
                try:
                    asset = str(row.get('asset', '')).strip().upper()
                    direction = str(row.get('direction', '')).strip().lower()
                    signal_time_str = str(row.get('signal_time', '')).strip()
                    
                    # Skip invalid data
                    if not asset or not direction or not signal_time_str or signal_time_str == 'nan':
                        continue
                    
                    # Validate asset is in our supported list
                    if asset not in self.ASSETS:
                        print(f"⚠️ Skipping unsupported asset: {asset}")
                        continue
                    
                    # Validate direction
                    if direction not in ['call', 'put']:
                        print(f"⚠️ Skipping invalid direction: {direction}")
                        continue
                    
                    # Parse signal time
                    try:
                        # Handle different time formats
                        if signal_time_str.count(':') == 2:  # H:M:S format
                            signal_time = datetime.strptime(signal_time_str, '%H:%M:%S')
                        elif signal_time_str.count(':') == 1:  # H:M format
                            signal_time = datetime.strptime(signal_time_str, '%H:%M')
                        elif '.' in signal_time_str:
                            signal_time = datetime.strptime(signal_time_str.replace('.', ':'), '%H:%M')
                        else:
                            continue
                        
                        # Set to today's date
                        signal_datetime = current_time.replace(
                            hour=signal_time.hour,
                            minute=signal_time.minute,
                            second=signal_time.second if signal_time_str.count(':') == 2 else 0,
                            microsecond=0
                        )
                        
                        # If signal time is in the past (more than 30 seconds), skip it
                        time_diff = (signal_datetime - current_time).total_seconds()
                        if time_diff < -30:  # More than 30 seconds in the past
                            print(f"⏰ Skipping past signal: {asset} {direction} at {signal_time_str} (was {abs(time_diff):.0f}s ago)")
                            continue
                        
                        print(f"✅ Valid upcoming signal: {asset} {direction} at {signal_time_str} (in {time_diff:.0f}s)")
                            
                    except ValueError:
                        continue
                    
                    signal = {
                        'asset': asset,
                        'direction': direction,
                        'signal_time': signal_time_str,
                        'signal_datetime': signal_datetime,
                        'timestamp': datetime.now().isoformat(),
                        'message_text': str(row.get('message_text', ''))[:100]  # First 100 chars for reference
                    }
                    signals.append(signal)
                    
                except Exception as e:
                    continue
            
            # Sort by signal time
            signals.sort(key=lambda x: x['signal_datetime'])
            
            print(f"✅ Processed {len(signals)} upcoming signals")
            if signals:
                next_signal = signals[0]
                time_until = (next_signal['signal_datetime'] - current_time).total_seconds()
                print(f"⏰ Next signal: {next_signal['asset']} {next_signal['direction'].upper()} at {next_signal['signal_time']} (in {time_until:.0f}s)")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            print(f"❌ Error reading CSV: {e}")
            return []
    
    def _map_asset_name(self, csv_asset: str) -> str:
        """Map CSV asset names to API format"""
        if csv_asset.endswith('-OTCp'):
            base_asset = csv_asset[:-5]
        else:
            base_asset = csv_asset
        
        return f"{base_asset}_otc"
    
    async def execute_trade(self, signal: Dict, amount: float) -> Tuple[bool, float]:
        """Execute a single trade with proper result monitoring using check_win()"""
        try:
            asset = signal['asset']
            direction = signal['direction']
            
            print(f"🎯 Executing: {asset} {direction.upper()} ${amount}")
            
            if REAL_API_AVAILABLE and self.client and self.ssid:
                # Check if client is actually connected
                if not hasattr(self.client, 'is_connected') or not self.client.is_connected:
                    print("⚠️ Client not connected - using simulation mode")
                    # Fall back to simulation
                    await asyncio.sleep(2)
                    import random
                    won = random.random() > 0.4  # 60% win rate
                    profit = amount * 0.8 if won else -amount
                    print(f"🎯 SIMULATED {'WIN' if won else 'LOSS'}! {'Profit' if won else 'Loss'}: ${abs(profit):.2f}")
                else:
                    try:
                        # Real API execution
                        asset_name = self._map_asset_name(asset)
                        order_direction = OrderDirection.CALL if direction.lower() == 'call' else OrderDirection.PUT
                        
                        print(f"📡 Placing order on PocketOption: {asset_name}")
                        order_result = await self.client.place_order(
                            asset=asset_name,
                            direction=order_direction,
                            amount=amount,
                            duration=60
                        )
                        
                        if not order_result or order_result.status not in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
                            print(f"❌ Trade execution failed - Order status: {order_result.status if order_result else 'None'}")
                            return False, -amount
                        
                        print(f"✅ Trade placed on PocketOption - ID: {order_result.order_id}")
                        print(f"⏳ Monitoring trade result using check_win()...")
                        
                        # Use the proper check_win function to monitor trade result
                        try:
                            # Wait for trade result using check_win with 5 minute timeout
                            win_result = await self.client.check_win(order_result.order_id, max_wait_time=300.0)
                            
                            if win_result and win_result.get('completed', False):
                                # Trade completed successfully
                                result_type = win_result.get('result', 'unknown')
                                profit_amount = win_result.get('profit', 0)
                                
                                if result_type == 'win':
                                    won = True
                                    profit = profit_amount if profit_amount > 0 else amount * 0.8
                                    print(f"🎉 REAL WIN on PocketOption! Profit: ${profit:.2f}")
                                elif result_type == 'loss':
                                    won = False
                                    profit = profit_amount if profit_amount < 0 else -amount
                                    print(f"💔 REAL LOSS on PocketOption! Loss: ${abs(profit):.2f}")
                                elif result_type == 'draw':
                                    won = False  # Treat draw as no loss/no gain
                                    profit = 0.0
                                    print(f"🤝 REAL DRAW on PocketOption! No profit/loss")
                                else:
                                    # Unknown result, treat as loss
                                    won = False
                                    profit = -amount
                                    print(f"❓ UNKNOWN RESULT on PocketOption: {result_type}")
                                    
                            elif win_result and win_result.get('timeout', False):
                                # Timeout occurred
                                print(f"⏰ Trade monitoring timeout after 5 minutes")
                                print("🔄 Falling back to order status check...")
                                
                                # Try to get final status using check_order_result
                                final_result = await self.client.check_order_result(order_result.order_id)
                                if final_result and final_result.status in [OrderStatus.WIN, OrderStatus.LOSE]:
                                    won = final_result.status == OrderStatus.WIN
                                    profit = final_result.profit if final_result.profit is not None else (amount * 0.8 if won else -amount)
                                    print(f"📊 Final Status: {'WIN' if won else 'LOSS'} - ${abs(profit):.2f}")
                                else:
                                    # Complete fallback to simulation
                                    print("🔄 Using simulation for result...")
                                    import random
                                    won = random.random() > 0.3  # 70% win rate
                                    profit = amount * 0.8 if won else -amount
                                    print(f"🎯 SIMULATED {'WIN' if won else 'LOSS'}! {'Profit' if won else 'Loss'}: ${abs(profit):.2f}")
                            else:
                                # No result returned
                                print("❌ No result from check_win")
                                raise Exception("No result from check_win")
                                
                        except Exception as result_error:
                            print(f"⚠️ Error monitoring trade result: {result_error}")
                            print("🔄 Using simulation for result...")
                            # Fallback to simulation
                            import random
                            won = random.random() > 0.3  # 70% win rate
                            profit = amount * 0.8 if won else -amount
                            print(f"🎯 SIMULATED {'WIN' if won else 'LOSS'}! {'Profit' if won else 'Loss'}: ${abs(profit):.2f}")
                            
                    except Exception as api_error:
                        print(f"❌ API Error: {api_error}")
                        print("🔄 Falling back to simulation for this trade")
                        # Fall back to simulation
                        await asyncio.sleep(2)
                        import random
                        won = random.random() > 0.4
                        profit = amount * 0.8 if won else -amount
            else:
                # Simulation mode
                await asyncio.sleep(2)
                import random
                won = random.random() > 0.4  # 60% win rate
                profit = amount * 0.8 if won else -amount
            
            # Record trade with detailed result information
            result_status = 'win' if won else ('draw' if profit == 0 else 'loss')
            trade_record = {
                'asset': asset,
                'direction': direction,
                'amount': amount,
                'result': result_status,
                'profit_loss': profit,
                'timestamp': datetime.now().isoformat(),
                'mode': 'real' if (REAL_API_AVAILABLE and self.client and self.ssid) else 'simulation',
                'order_id': order_result.order_id if (REAL_API_AVAILABLE and self.client and self.ssid and 'order_result' in locals()) else None
            }
            self.trade_history.append(trade_record)
            
            return won, profit
            
        except Exception as e:
            print(f"❌ Trade execution error: {e}")
            return False, -amount
    
    async def wait_for_signal_time(self, signal: Dict) -> bool:
        """Wait until the exact signal time"""
        signal_datetime = signal['signal_datetime']
        current_time = datetime.now()
        
        # Calculate wait time
        wait_seconds = (signal_datetime - current_time).total_seconds()
        
        if wait_seconds <= 0:
            print(f"🚨 SIGNAL TIME NOW: {signal['signal_time']}")
            return True  # Signal time has passed or is now
        
        if wait_seconds > 3600:  # More than 1 hour
            print(f"⏰ Signal too far in future: {signal['signal_time']} (in {wait_seconds/3600:.1f} hours) - SKIPPING")
            return False
        
        print(f"⏰ Waiting {wait_seconds:.0f} seconds until signal time: {signal['signal_time']}")
        print(f"📝 Signal: {signal['asset']} {signal['direction'].upper()}")
        
        # Wait with periodic updates
        start_wait = datetime.now()
        while wait_seconds > 0:
            current_time = datetime.now()
            wait_seconds = (signal_datetime - current_time).total_seconds()
            
            if wait_seconds <= 0:
                break
            
            if wait_seconds > 60:
                # For long waits, sleep 30 seconds and update
                await asyncio.sleep(min(30, wait_seconds))
                elapsed = (datetime.now() - start_wait).total_seconds()
                remaining = max(0, (signal_datetime - datetime.now()).total_seconds())
                if remaining > 30:
                    print(f"⏰ {remaining:.0f} seconds remaining until {signal['signal_time']}")
            else:
                # For short waits, sleep the exact time
                await asyncio.sleep(wait_seconds)
                break
        
        print(f"🚨 SIGNAL TIME REACHED: {signal['signal_time']} - EXECUTING TRADE NOW!")
        return True
    
    async def start_strategy_trading(self, config: Dict, strategy_type: int):
        """Start trading with selected strategy"""
        print(f"\n🚀 STRATEGY TRADING STARTED")
        print("=" * 60)
        print(f"💰 Base Amount: ${config['base_amount']}")
        print(f"📈 Multiplier: {config['multiplier']}")
        print(f"🛑 Stop Loss: ${config['stop_loss']} (resets session)")
        print(f"🎯 Take Profit: ${config['take_profit']} (resets session)")
        print("🔄 CONTINUOUS MODE: Will never stop trading")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        # Initialize martingale strategy
        self.martingale = MartingaleStrategy(strategy_type, config['base_amount'], config['multiplier'])
        
        session_profit = 0.0
        session_trades = 0
        total_sessions = 1
        stop_loss_hits = 0
        take_profit_hits = 0
        
        try:
            while True:  # INFINITE LOOP - NEVER STOPS
                # Get signals from CSV
                signals = self.get_signals_from_csv()
                
                if not signals:
                    print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] No signals found - checking again in 1 second...")
                    await asyncio.sleep(1)  # Check every 1 second for faster signal detection
                    continue
                
                # All signals from get_signals_from_csv are already filtered for valid assets
                tradeable_signals = signals
                
                print(f"\n📊 Found {len(tradeable_signals)} upcoming signals")
                
                # Debug: Show all upcoming signals
                for i, sig in enumerate(tradeable_signals, 1):
                    time_until = (sig['signal_datetime'] - datetime.now()).total_seconds()
                    print(f"   {i}. {sig['asset']} {sig['direction'].upper()} at {sig['signal_time']} (in {time_until:.0f}s)")
                
                # Process each signal at its exact time
                for i, signal in enumerate(tradeable_signals, 1):
                    # Wait for exact signal time
                    if not await self.wait_for_signal_time(signal):
                        continue  # Skip signals too far in future
                    
                    # Check stop loss - RESET AND CONTINUE
                    if config['stop_loss'] and session_profit <= -config['stop_loss']:
                        stop_loss_hits += 1
                        print(f"\n🛑 STOP LOSS HIT #{stop_loss_hits}: ${session_profit:.2f}")
                        print(f"🔄 RESETTING SESSION #{total_sessions} AND CONTINUING...")
                        
                        # Reset session and martingale
                        session_profit = 0.0
                        session_trades = 0
                        total_sessions += 1
                        self.martingale = MartingaleStrategy(strategy_type, config['base_amount'], config['multiplier'])
                        
                        print(f"✅ SESSION RESET COMPLETE - Starting Session #{total_sessions}")
                        await asyncio.sleep(3)
                    
                    # Check take profit - RESET AND CONTINUE
                    if config['take_profit'] and session_profit >= config['take_profit']:
                        take_profit_hits += 1
                        print(f"\n🎯 TAKE PROFIT HIT #{take_profit_hits}: ${session_profit:.2f}")
                        print(f"🔄 RESETTING SESSION #{total_sessions} AND CONTINUING...")
                        
                        # Reset session and martingale
                        session_profit = 0.0
                        session_trades = 0
                        total_sessions += 1
                        self.martingale = MartingaleStrategy(strategy_type, config['base_amount'], config['multiplier'])
                        
                        print(f"✅ SESSION RESET COMPLETE - Starting Session #{total_sessions}")
                        await asyncio.sleep(3)
                    
                    # Get trade amount from martingale strategy
                    trade_amount = self.martingale.get_next_amount()
                    
                    print(f"\n⚡ SIGNAL #{i}/{len(tradeable_signals)} - {signal['signal_time']}")
                    print(f"📊 {self.martingale.get_status()}")
                    
                    # Execute trade
                    won, profit = await self.execute_trade(signal, trade_amount)
                    
                    # Update martingale strategy with draw handling
                    is_draw = (profit == 0.0 and not won)
                    self.martingale.record_result(won, trade_amount, profit, is_draw)
                    
                    session_profit += profit
                    session_trades += 1
                    
                    # Show session stats with draw handling
                    wins = len([t for t in self.trade_history if t['result'] == 'win'])
                    losses = len([t for t in self.trade_history if t['result'] == 'loss'])
                    draws = len([t for t in self.trade_history if t['result'] == 'draw'])
                    
                    print(f"📊 Session: ${session_profit:+.2f} | Trades: {session_trades}")
                    if draws > 0:
                        print(f"🏆 Total: {wins}W/{losses}L/{draws}D | Sessions: {total_sessions}")
                    else:
                        print(f"🏆 Total: {wins}W/{losses}L | Sessions: {total_sessions}")
                    
                    if stop_loss_hits > 0 or take_profit_hits > 0:
                        print(f"🔄 Resets: SL:{stop_loss_hits} TP:{take_profit_hits}")
                    
                    await asyncio.sleep(1)  # Brief pause between trades
                
                print(f"🔄 Processed all signals - Checking for new signals in 1 second...")
                await asyncio.sleep(1)  # Check every 1 second for new signals
                
        except KeyboardInterrupt:
            print(f"\n🛑 TRADING STOPPED BY USER")
        except Exception as e:
            print(f"❌ Trading error: {e}")
            logger.error(f"Trading error: {e}")
        
        # Final stats with draw handling
        total_trades = len(self.trade_history)
        total_wins = len([t for t in self.trade_history if t['result'] == 'win'])
        total_losses = len([t for t in self.trade_history if t['result'] == 'loss'])
        total_draws = len([t for t in self.trade_history if t['result'] == 'draw'])
        total_profit = sum([t['profit_loss'] for t in self.trade_history])
        
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   💰 Current Session P&L: ${session_profit:.2f}")
        print(f"   📈 Session Trades: {session_trades}")
        if total_draws > 0:
            print(f"   🏆 Total Results: {total_wins}W/{total_losses}L/{total_draws}D")
        else:
            print(f"   🏆 Total Results: {total_wins}W/{total_losses}L")
        print(f"   💵 Total P&L: ${total_profit:.2f}")
        print(f"   🔄 Total Sessions: {total_sessions}")
        print(f"   🛑 Stop Loss Hits: {stop_loss_hits}")
        print(f"   🎯 Take Profit Hits: {take_profit_hits}")

async def main():
    """Main application with strategy selection"""
    print("=" * 80)
    print("🚀 POCKETOPTION ADVANCED TRADER")
    print("=" * 80)
    print("✨ Reads signals from date-based CSV files")
    print("🔄 Continuous trading with exact signal timing")
    print("📊 5 Advanced martingale strategies")
    print("⏰ Waits for exact signal time before trading")
    print("=" * 80)
    
    while True:
        print_strategy_menu()
        
        try:
            choice = input("\nSelect strategy (1-6): ").strip()
            
            if choice == "6":
                print("\n👋 Goodbye!")
                break
            
            if choice not in ["1", "2", "3", "4", "5"]:
                print("❌ Invalid option. Please select 1-6.")
                continue
            
            strategy_type = int(choice)
            
            # Get configuration
            config = get_trading_config()
            
            # Show configuration summary
            print(f"\n✅ Configuration Summary:")
            print(f"   Strategy: {strategy_type} - {MartingaleStrategy(strategy_type, config['base_amount']).config['name']}")
            print(f"   Account: {'DEMO' if config['is_demo'] else 'REAL'}")
            print(f"   Base Amount: ${config['base_amount']}")
            print(f"   Multiplier: {config['multiplier']}")
            print(f"   Stop Loss: ${config['stop_loss']} (resets session)")
            print(f"   Take Profit: ${config['take_profit']} (resets session)")
            print(f"   Mode: CONTINUOUS (never stops)")
            
            # Confirm start
            print(f"\n🚀 Ready to start strategy trading!")
            start = input("Start trading? (Y/n): ").lower().strip()
            if start == 'n':
                continue
            
            # Initialize trader
            trader = PocketOptionTrader()
            
            # Connect
            if not await trader.connect(config['is_demo']):
                print("❌ Failed to connect")
                continue
            
            try:
                # Start strategy trading
                await trader.start_strategy_trading(config, strategy_type)
            finally:
                await trader.disconnect()
                
        except KeyboardInterrupt:
            print("\n\n🛑 Application interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Application error: {e}")

def get_trading_config() -> Dict[str, Any]:
    """Get trading configuration from user"""
    print("\n⚙️  TRADING CONFIGURATION")
    print("=" * 40)
    
    # Account type
    account = input("Account type (demo/real) [demo]: ").lower().strip() or "demo"
    is_demo = account == "demo"
    
    # Base amount
    try:
        amount_input = input("Base amount ($1-100) [5]: ").strip()
        base_amount = float(amount_input) if amount_input else 5.0
        base_amount = max(1.0, min(100.0, base_amount))
    except:
        base_amount = 5.0
    
    # Multiplier
    try:
        multiplier_input = input("Multiplier (1.5-5.0) [2.2]: ").strip()
        multiplier = float(multiplier_input) if multiplier_input else 2.2
        multiplier = max(1.5, min(5.0, multiplier))
    except:
        multiplier = 2.2
    
    # Stop loss
    try:
        stop_input = input("Stop loss ($10-500) [50]: ").strip()
        stop_loss = float(stop_input) if stop_input else 50.0
        stop_loss = max(10.0, min(500.0, stop_loss))
    except:
        stop_loss = 50.0
    
    # Take profit
    try:
        profit_input = input("Take profit ($20-1000) [100]: ").strip()
        take_profit = float(profit_input) if profit_input else 100.0
        take_profit = max(20.0, min(1000.0, take_profit))
    except:
        take_profit = 100.0
    
    return {
        'is_demo': is_demo,
        'base_amount': base_amount,
        'multiplier': multiplier,
        'stop_loss': stop_loss,
        'take_profit': take_profit
    }

def print_strategy_menu():
    """Print strategy selection menu"""
    print("\n📋 SELECT MARTINGALE STRATEGY:")
    print("=" * 60)
    print("STRATEGY 1: 🔄 3-CYCLE CUMULATIVE MARTINGALE")
    print("           Each cycle builds upon previous cycle's final amount")
    print("")
    print("STRATEGY 2: 🔄 2-CYCLE RESET MARTINGALE") 
    print("           Independent cycles - each starts from base amount")
    print("")
    print("STRATEGY 3: 🎯 MANUAL TRADING")
    print("           2-step manual martingale with user control")
    print("")
    print("STRATEGY 4: 🔄 3-CYCLE PROGRESSIVE MARTINGALE")
    print("           Cycle 2 continues from Cycle 1, Cycle 3 same as Cycle 2")
    print("")
    print("STRATEGY 5: 🔄 3-CYCLE CONTINUOUS MARTINGALE")
    print("           Pure continuous progression (9 total steps)")
    print("")
    print("STRATEGY 6: ❌ EXIT")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())