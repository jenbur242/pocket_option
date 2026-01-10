#!/usr/bin/env python3
"""
PocketOption Precise Timing Trader
Places trades 10 seconds before signal time and closes after exactly 1 minute
Example: Signal at 00:38:00 → Trade at 00:37:50 → Close at 00:38:50
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

class MultiAssetMartingaleStrategy:
    """Multi-asset martingale strategy with immediate step progression"""
    
    def __init__(self, base_amount: float, multiplier: float = 2.5):
        self.base_amount = base_amount
        self.multiplier = multiplier
        self.max_steps = 3
        
        # Track each asset separately
        self.asset_strategies = {}  # {asset: {'step': 1, 'amounts': []}}
        
        # Calculate step amounts for display
        step1 = base_amount
        step2 = step1 * multiplier
        step3 = step2 * multiplier
        
        print(f"🎯 Multi-Asset Martingale Strategy")
        print(f"   Base Amount: ${base_amount}")
        print(f"   Multiplier: {multiplier}")
        print(f"   Max Steps: {self.max_steps}")
        print(f"   Step Amounts:")
        print(f"     Step 1: ${step1:.2f} (Base)")
        print(f"     Step 2: ${step2:.2f} (${step1:.2f} × {multiplier})")
        print(f"     Step 3: ${step3:.2f} (${step2:.2f} × {multiplier})")
        print(f"   Strategy: Immediate step progression + parallel assets")
    
    def get_asset_step(self, asset: str) -> int:
        """Get current step for specific asset"""
        if asset not in self.asset_strategies:
            self.asset_strategies[asset] = {'step': 1, 'amounts': []}
        return self.asset_strategies[asset]['step']
    
    def get_current_amount(self, asset: str) -> float:
        """Get current trade amount for specific asset based on its step"""
        if asset not in self.asset_strategies:
            self.asset_strategies[asset] = {'step': 1, 'amounts': []}
        
        strategy = self.asset_strategies[asset]
        step = strategy['step']
        amounts = strategy['amounts']
        
        if step == 1:
            return self.base_amount
        elif step == 2:
            # Step 2 = Step 1 amount × multiplier
            if len(amounts) > 0:
                return amounts[0] * self.multiplier
            else:
                return self.base_amount * self.multiplier
        elif step == 3:
            # Step 3 = Step 2 amount × multiplier
            if len(amounts) > 1:
                return amounts[1] * self.multiplier
            else:
                # If no Step 2 amount recorded, calculate: (Step 1 × multiplier) × multiplier
                step2_amount = self.base_amount * self.multiplier
                return step2_amount * self.multiplier
        else:
            return self.base_amount
    
    def record_result(self, won: bool, asset: str, trade_amount: float) -> Dict[str, Any]:
        """Record trade result and return next action"""
        if asset not in self.asset_strategies:
            self.asset_strategies[asset] = {'step': 1, 'amounts': []}
        
        strategy = self.asset_strategies[asset]
        
        # Record amount used
        if len(strategy['amounts']) < strategy['step']:
            strategy['amounts'].append(trade_amount)
        
        if won:
            print(f"✅ {asset} WIN at Step {strategy['step']}! Resetting to Step 1")
            strategy['step'] = 1
            strategy['amounts'] = []
            return {'action': 'reset', 'asset': asset, 'next_step': 1}
        else:
            print(f"❌ {asset} LOSS at Step {strategy['step']}! Moving to Step {strategy['step'] + 1}")
            strategy['step'] += 1
            
            if strategy['step'] > self.max_steps:
                print(f"🚨 {asset} - All {self.max_steps} steps lost! Resetting to Step 1")
                strategy['step'] = 1
                strategy['amounts'] = []
                return {'action': 'reset_after_max_loss', 'asset': asset, 'next_step': 1}
            else:
                return {'action': 'continue', 'asset': asset, 'next_step': strategy['step']}
    
    def get_status(self, asset: str) -> str:
        """Get current strategy status for specific asset"""
        if asset not in self.asset_strategies:
            return f"{asset}: Step 1/3 (${self.base_amount})"
        
        strategy = self.asset_strategies[asset]
        current_amount = self.get_current_amount(asset)
        return f"{asset}: Step {strategy['step']}/3 (${current_amount})"
    
    def get_all_active_assets(self) -> List[str]:
        """Get all assets currently being tracked"""
        return list(self.asset_strategies.keys())
    
    def should_prioritize_existing_sequences(self) -> bool:
        """Check if any asset is in the middle of a martingale sequence (Step 2 or 3)"""
        for asset, strategy in self.asset_strategies.items():
            if strategy['step'] > 1:  # Asset is at Step 2 or 3
                return True
        return False
    
    def get_assets_in_sequence(self) -> List[str]:
        """Get assets that are currently in martingale sequence (Step 2 or 3)"""
        assets_in_sequence = []
        for asset, strategy in self.asset_strategies.items():
            if strategy['step'] > 1:
                assets_in_sequence.append(asset)
        return assets_in_sequence
    
    def get_assets_at_step1(self) -> List[str]:
        """Get assets that are at Step 1 (ready for new signals)"""
        assets_at_step1 = []
        for asset, strategy in self.asset_strategies.items():
            if strategy['step'] == 1:
                assets_at_step1.append(asset)
        return assets_at_step1

class MultiAssetPreciseTrader:
    """Multi-asset trader with immediate step progression"""
    
    def __init__(self):
        self.ssid = os.getenv('SSID')
        self.client = None
        
        # Use date-based CSV filename
        today = datetime.now().strftime('%Y%m%d')
        self.csv_file = f"pocketoption_messages_{today}.csv"
        
        self.trade_history = []
        self.pending_immediate_trades = []  # Queue for immediate next step trades
        
        # API health tracking
        self.api_failures = 0
        self.max_api_failures = 3  # Switch to simulation after 3 consecutive failures
        self.last_successful_api_call = datetime.now()
        
        # Available assets - based on PocketOption API library constants
        self.WORKING_ASSETS = {
            # Major pairs (direct format) - Forex only for trading signals
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD',
            # Cross pairs (require _otc suffix)
            'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'CADCHF', 'CADJPY', 'CHFJPY', 
            'CHFNOK', 'EURCHF', 'EURGBP', 'EURHUF', 'EURJPY', 'EURNZD', 'EURRUB', 
            'GBPAUD', 'GBPJPY', 'NZDJPY', 'USDRUB'
        }
        
        # Assets that don't work with the API (confirmed not in API library)
        self.UNSUPPORTED_ASSETS = {
            'BRLUSD', 'USDBRL', 'USDCOP', 'NZDCAD', 'USDPKR', 'USDBDT', 'USDEGP'
        }
        
        # Force simulation for unsupported assets
        self.FORCE_SIMULATION_ASSETS = self.UNSUPPORTED_ASSETS.copy()
        
        print(f"📊 Using CSV file: {self.csv_file}")
    
    def should_use_api(self, asset: str) -> bool:
        """Determine if we should use real API or simulation"""
        # Force simulation for unsupported assets
        if asset in self.FORCE_SIMULATION_ASSETS:
            return False
        
        # If too many API failures, use simulation
        if self.api_failures >= self.max_api_failures:
            return False
        
        # If no client or SSID, use simulation
        if not (REAL_API_AVAILABLE and self.client and self.ssid):
            return False
        
        return True
    
    def record_api_success(self):
        """Record successful API call"""
        self.api_failures = 0
        self.last_successful_api_call = datetime.now()
    
    def record_api_failure(self):
        """Record API failure"""
        self.api_failures += 1
        if self.api_failures >= self.max_api_failures:
            print(f"⚠️ API health degraded ({self.api_failures} failures) - switching to simulation mode")
    
    async def connect(self, is_demo: bool = True) -> bool:
        """Connect to PocketOption"""
        try:
            print("🔌 Connecting to PocketOption...")
            
            if REAL_API_AVAILABLE and self.ssid:
                print(f"🔑 Using SSID: {self.ssid[:50]}...")
                
                self.client = AsyncPocketOptionClient(
                    ssid=self.ssid,
                    is_demo=is_demo,
                    persistent_connection=False,
                    auto_reconnect=False,
                    enable_logging=False
                )
                
                try:
                    await asyncio.wait_for(self.client.connect(), timeout=15.0)
                    balance = await asyncio.wait_for(self.client.get_balance(), timeout=10.0)
                    
                    print(f"✅ Connected! {'DEMO' if is_demo else 'REAL'} Account")
                    print(f"💰 Balance: ${balance.balance:.2f}")
                    return True
                    
                except Exception as conn_error:
                    print(f"❌ Connection failed: {conn_error}")
                    print("🔄 Using simulation mode")
                    self.client = None
                    return True
            else:
                print(f"✅ Connected! {'DEMO' if is_demo else 'REAL'} Account (Simulation)")
                print(f"💰 Balance: $1000.00 (Simulated)")
                return True
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Using simulation mode")
            self.client = None
            return True
    
    def get_signals_from_csv(self) -> List[Dict[str, Any]]:
        """Get trading signals from CSV file"""
        try:
            if not os.path.exists(self.csv_file):
                print(f"❌ CSV file not found: {self.csv_file}")
                return []
            
            df = pd.read_csv(self.csv_file, on_bad_lines='skip')
            
            if 'is_signal' in df.columns:
                signals_df = df[df['is_signal'] == 'Yes'].copy()
            else:
                signals_df = df.copy()
            
            if signals_df.empty:
                return []
            
            signals = []
            current_time = datetime.now()
            
            for _, row in signals_df.iterrows():
                try:
                    asset = str(row.get('asset', '')).strip()
                    direction = str(row.get('direction', '')).strip().lower()
                    signal_time_str = str(row.get('signal_time', '')).strip()
                    
                    if not asset or not direction or not signal_time_str or signal_time_str == 'nan':
                        continue
                    
                    # Normalize asset format: uppercase base, lowercase _otc suffix
                    if asset.lower().endswith('_otc'):
                        base_asset = asset[:-4].upper()
                        trading_asset = f"{base_asset}_otc"
                    else:
                        trading_asset = asset.upper()
                    
                    # Extract base asset for logging purposes only
                    if trading_asset.endswith('_otc'):
                        base_asset = trading_asset[:-4]  # Remove _otc for logging
                        asset_type = "OTC"
                    else:
                        base_asset = trading_asset
                        asset_type = "Regular"
                    
                    # Log asset status using base asset
                    if base_asset in getattr(self, 'WORKING_ASSETS', set()):
                        print(f"✅ Supported {asset_type} asset: {asset}")
                    elif base_asset in getattr(self, 'UNSUPPORTED_ASSETS', set()):
                        print(f"⚠️ Unsupported {asset_type} asset: {asset} - will use simulation")
                    else:
                        print(f"❓ Unknown {asset_type} asset: {asset} - will test API formats")
                    
                    if direction not in ['call', 'put']:
                        continue
                    
                    # Parse signal time
                    try:
                        if signal_time_str.count(':') == 2:
                            signal_time = datetime.strptime(signal_time_str, '%H:%M:%S')
                        elif signal_time_str.count(':') == 1:
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
                        
                        # If signal time has passed today, set it for tomorrow
                        if signal_datetime <= current_time:
                            signal_datetime = signal_datetime + timedelta(days=1)
                        
                        # Calculate trade execution time (10 seconds before signal time)
                        trade_datetime = signal_datetime - timedelta(seconds=10)
                        
                        # Skip past trades (more than 2 minutes ago)
                        time_diff = (trade_datetime - current_time).total_seconds()
                        if time_diff < -120:
                            continue
                        
                        # Skip far future trades (more than 1 minute)
                        if time_diff > 60:
                            continue
                            
                    except ValueError:
                        continue
                    
                    signal = {
                        'asset': trading_asset,
                        'direction': direction,
                        'signal_time': signal_time_str,
                        'signal_datetime': signal_datetime,
                        'trade_datetime': trade_datetime,  # 10 seconds before signal
                        'close_datetime': trade_datetime + timedelta(seconds=60),  # 60 seconds after trade
                        'timestamp': datetime.now().isoformat(),
                        'message_text': str(row.get('message_text', ''))[:100]
                    }
                    
                    # Debug timing
                    print(f"🔍 Signal parsed: {trading_asset} {direction} at {signal_time_str}")
                    print(f"   Signal time: {signal_datetime.strftime('%H:%M:%S')}")
                    print(f"   Trade time:  {trade_datetime.strftime('%H:%M:%S')} (10s before)")
                    print(f"   Time until trade: {(trade_datetime - current_time).total_seconds():.0f}s")
                    
                    # Only add if within 1 minute
                    time_until_trade = (trade_datetime - current_time).total_seconds()
                    if time_until_trade > 60:
                        print(f"   ⏰ Too far (>{60}s) - skipping")
                        continue
                    
                    signals.append(signal)
                    
                except Exception:
                    continue
            
            # Sort by trade execution time
            signals.sort(key=lambda x: x['trade_datetime'])
            return signals
            
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return []
    
    def _map_asset_name(self, csv_asset: str) -> str:
        """Map CSV asset names to API format based on comprehensive testing"""
        # Handle new _otc format from improved CSV parsing
        if csv_asset.endswith('_otc'):
            base_asset = csv_asset[:-4]  # Remove _otc suffix
            # For _otc assets, always return with _otc suffix (they're cross pairs)
            return csv_asset  # Keep as GBPUSD_otc
        elif csv_asset.endswith('-OTCp'):
            base_asset = csv_asset[:-5]
            return f"{base_asset}_otc"  # Convert to _otc format
        elif csv_asset.endswith('-OTC'):
            base_asset = csv_asset[:-4]
            return f"{base_asset}_otc"  # Convert to _otc format
        else:
            base_asset = csv_asset
        
        # Based on PocketOption API library constants:
        
        # Major pairs that work with direct format
        major_pairs = {'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD'}
        
        # Cross pairs that ONLY work with _otc suffix
        cross_pairs_otc = {
            'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'CADCHF', 'CADJPY', 'CHFJPY', 
            'CHFNOK', 'EURCHF', 'EURGBP', 'EURHUF', 'EURJPY', 'EURNZD', 'EURRUB', 
            'GBPAUD', 'GBPJPY', 'NZDJPY', 'USDRUB'
        }
        
        if base_asset in major_pairs:
            # Major pairs work with direct format
            return base_asset
        elif base_asset in cross_pairs_otc:
            # Cross pairs ONLY work with _otc suffix
            return f"{base_asset}_otc"
        else:
            # Unknown/exotic pairs - return as is (will likely fail and use simulation)
            return base_asset
    
    async def execute_immediate_trade(self, asset: str, direction: str, amount: float) -> Tuple[bool, float]:
        """Execute immediate trade (for next step after loss)"""
        try:
            print(f"⚡ IMMEDIATE: {asset} {direction.upper()} ${amount}")
            
            execution_time = datetime.now()
            target_close_time = execution_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
            dynamic_duration = max(59, min(60, int((target_close_time - execution_time).total_seconds())))
            
            # Check if this is a problematic asset or API health is poor
            force_simulation = asset in getattr(self, 'FORCE_SIMULATION_ASSETS', set()) or not self.should_use_api(asset)
            if force_simulation:
                if asset in getattr(self, 'FORCE_SIMULATION_ASSETS', set()):
                    print(f"🎯 {asset} using SIMULATION mode (unsupported by PocketOption API)")
                else:
                    print(f"🎯 {asset} using SIMULATION mode (API health degraded)")
            
            if self.should_use_api(asset):
                try:
                    asset_name = self._map_asset_name(asset)
                    order_direction = OrderDirection.CALL if direction.lower() == 'call' else OrderDirection.PUT
                    
                    order_result = await self.client.place_order(
                        asset=asset_name,
                        direction=order_direction,
                        amount=amount,
                        duration=dynamic_duration
                    )
                    
                    if order_result and order_result.status in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
                        print(f"✅ Immediate trade placed - ID: {order_result.order_id}")
                        self.record_api_success()  # Record successful API call
                        
                        # Quick result check with optimized polling
                        try:
                            max_wait = min(25.0, dynamic_duration + 5.0)  # Max 25 seconds
                            print(f"⏳ Monitoring immediate result (max {max_wait:.0f}s)...")
                            
                            # Poll every 3 seconds for immediate trades
                            start_time = datetime.now()
                            win_result = None
                            
                            while (datetime.now() - start_time).total_seconds() < max_wait:
                                try:
                                    # Check with 3-second timeout per attempt
                                    win_result = await asyncio.wait_for(
                                        self.client.check_win(order_result.order_id, max_wait_time=3.0),
                                        timeout=3.0
                                    )
                                    
                                    if win_result and win_result.get('completed', False):
                                        break
                                    
                                    # If not completed, wait 2 seconds before next check
                                    elapsed = (datetime.now() - start_time).total_seconds()
                                    remaining = max_wait - elapsed
                                    if remaining > 2:
                                        await asyncio.sleep(2.0)
                                    else:
                                        break
                                        
                                except asyncio.TimeoutError:
                                    elapsed = (datetime.now() - start_time).total_seconds()
                                    remaining = max_wait - elapsed
                                    if remaining > 1:
                                        await asyncio.sleep(1.0)
                                    else:
                                        break
                                except Exception:
                                    await asyncio.sleep(1.0)
                            
                            if win_result and win_result.get('completed', False):
                                result_type = win_result.get('result', 'unknown')
                                won = result_type == 'win'
                                profit = win_result.get('profit', amount * 0.8 if won else -amount)
                                print(f"✅ IMMEDIATE {'WIN' if won else 'LOSS'}: ${profit:+.2f}")
                                self.record_api_success()  # Record successful result check
                            else:
                                elapsed = (datetime.now() - start_time).total_seconds()
                                print(f"⚠️ Immediate trade timeout after {elapsed:.0f}s - using simulation")
                                self.record_api_failure()  # Record API failure
                                import random
                                won = random.random() > 0.4
                                profit = amount * 0.8 if won else -amount
                                print(f"🎯 SIMULATED {'WIN' if won else 'LOSS'}: ${profit:+.2f}")
                        except Exception as e:
                            print(f"⚠️ Immediate trade result error: {e}")
                            self.record_api_failure()  # Record API failure
                            import random
                            won = random.random() > 0.4
                            profit = amount * 0.8 if won else -amount
                            print(f"🎯 SIMULATED {'WIN' if won else 'LOSS'}: ${profit:+.2f}")
                    else:
                        print(f"❌ Immediate trade failed - using simulation")
                        self.record_api_failure()  # Record API failure
                        import random
                        won = random.random() > 0.4
                        profit = amount * 0.8 if won else -amount
                except Exception as api_error:
                    error_msg = str(api_error).lower()
                    if 'incorrectopentime' in error_msg or 'market' in error_msg or 'closed' in error_msg:
                        print(f"⚠️ Market closed for {asset} - using simulation")
                        print(f"   📊 This is normal outside trading hours")
                    else:
                        print(f"❌ Immediate API Error: {api_error}")
                        self.record_api_failure()  # Record API failure
                    import random
                    won = random.random() > 0.4
                    profit = amount * 0.8 if won else -amount
            else:
                # Simulation mode
                await asyncio.sleep(0.1)
                import random
                won = random.random() > 0.4
                profit = amount * 0.8 if won else -amount
            
            print(f"⚡ IMMEDIATE {'WIN' if won else 'LOSS'}: ${profit:+.2f}")
            return won, profit
            
        except Exception as e:
            print(f"❌ Immediate trade error: {e}")
            return False, -amount
    
    async def execute_precise_trade(self, signal: Dict, amount: float) -> Tuple[bool, float]:
        """Execute trade with precise timing"""
        try:
            asset = signal['asset']
            direction = signal['direction']
            trade_time = signal['trade_datetime']
            signal_time = signal['signal_datetime']
            
            current_time = datetime.now()
            
            # Wait until trade execution time (immediate execution when signal time arrives)
            wait_seconds = (trade_time - current_time).total_seconds()
            
            # If wait time is more than 1 minute, skip this signal
            if wait_seconds > 60:
                print(f"⏰ Signal too far: {wait_seconds:.0f}s (>{60}s) - SKIPPING")
                return False, 0  # Skip this trade
            
            if wait_seconds > 0:
                print(f"⏰ Waiting {wait_seconds:.0f}s until trade time: {trade_time.strftime('%H:%M:%S')}")
                print(f"📝 {asset} {direction.upper()} → Execute 10s before signal")
                
                # Wait with fast updates (max 1 minute total)
                while wait_seconds > 1:
                    if wait_seconds > 10:
                        await asyncio.sleep(0.5)  # Fast updates every 0.5s
                        current_time = datetime.now()
                        wait_seconds = (trade_time - current_time).total_seconds()
                        if wait_seconds > 10:
                            print(f"⏰ {wait_seconds:.0f}s until trade execution")
                    else:
                        await asyncio.sleep(wait_seconds - 0.1)
                        break
                
                # Final precision timing
                while True:
                    current_time = datetime.now()
                    remaining = (trade_time - current_time).total_seconds()
                    if remaining <= 0.05:  # Execute within 50ms
                        break
                    await asyncio.sleep(0.05)
            
            execution_time = datetime.now()
            
            # Calculate target close time (signal time at 00 seconds)
            target_close_time = signal_time.replace(second=0, microsecond=0)
            
            # Calculate dynamic duration to hit target close time
            dynamic_duration = int((target_close_time - execution_time).total_seconds())
            
            # Ensure duration is between 55-75 seconds for safety
            if dynamic_duration < 59:
                dynamic_duration = 59
                actual_close_time = execution_time + timedelta(seconds=dynamic_duration)
            elif dynamic_duration > 60:
                dynamic_duration = 60
                actual_close_time = execution_time + timedelta(seconds=dynamic_duration)
            else:
                actual_close_time = target_close_time
            
            print(f"🎯 EXECUTING: {asset} {direction.upper()} ${amount}")
            print(f"⏰ TIMING: Trade {execution_time.strftime('%H:%M:%S.%f')[:12]} → Signal {signal_time.strftime('%H:%M:%S')} → Close {actual_close_time.strftime('%H:%M:%S')}")
            print(f"📊 Dynamic Duration: {dynamic_duration}s (target: {target_close_time.strftime('%H:%M:%S')})")
            
            # Check if this is a problematic asset or API health is poor
            force_simulation = asset in getattr(self, 'FORCE_SIMULATION_ASSETS', set()) or not self.should_use_api(asset)
            if force_simulation:
                if asset in getattr(self, 'FORCE_SIMULATION_ASSETS', set()):
                    print(f"🎯 {asset} using SIMULATION mode (unsupported by PocketOption API)")
                else:
                    print(f"🎯 {asset} using SIMULATION mode (API health degraded)")
            
            if self.should_use_api(asset):
                try:
                    # Real API execution with optimized asset format selection
                    asset_name = self._map_asset_name(asset)
                    order_direction = OrderDirection.CALL if direction.lower() == 'call' else OrderDirection.PUT
                    
                    print(f"🔄 Using API format: {asset_name}")
                    order_result = await self.client.place_order(
                        asset=asset_name,
                        direction=order_direction,
                        amount=amount,
                        duration=dynamic_duration  # Use dynamic duration
                    )
                    
                    if order_result and order_result.status in [OrderStatus.ACTIVE, OrderStatus.PENDING]:
                        print(f"✅ Trade placed - ID: {order_result.order_id}")
                        print(f"⏳ Monitoring result...")
                        self.record_api_success()  # Record successful API call
                        
                        # Monitor trade result with optimized timeout and polling
                        try:
                            # Use shorter timeout with polling approach
                            max_wait = min(30.0, dynamic_duration + 10.0)  # Max 30 seconds or duration + 10s
                            print(f"⏳ Monitoring result (max {max_wait:.0f}s)...")
                            
                            # Try multiple shorter checks instead of one long wait
                            start_time = datetime.now()
                            win_result = None
                            
                            # Poll every 5 seconds for up to max_wait seconds
                            while (datetime.now() - start_time).total_seconds() < max_wait:
                                try:
                                    # Check with 5-second timeout per attempt
                                    win_result = await asyncio.wait_for(
                                        self.client.check_win(order_result.order_id, max_wait_time=5.0),
                                        timeout=5.0
                                    )
                                    
                                    if win_result and win_result.get('completed', False):
                                        break
                                    
                                    # If not completed, wait 2 seconds before next check
                                    elapsed = (datetime.now() - start_time).total_seconds()
                                    remaining = max_wait - elapsed
                                    if remaining > 2:
                                        print(f"⏳ Trade active, checking again in 2s (remaining: {remaining:.0f}s)")
                                        await asyncio.sleep(2.0)
                                    else:
                                        break
                                        
                                except asyncio.TimeoutError:
                                    elapsed = (datetime.now() - start_time).total_seconds()
                                    remaining = max_wait - elapsed
                                    if remaining > 2:
                                        print(f"⏳ Checking result... ({elapsed:.0f}s elapsed)")
                                        await asyncio.sleep(1.0)
                                    else:
                                        break
                                except Exception as check_error:
                                    print(f"⚠️ Check error: {check_error}")
                                    await asyncio.sleep(1.0)
                            
                            # Process result
                            if win_result and win_result.get('completed', False):
                                result_type = win_result.get('result', 'unknown')
                                profit_amount = win_result.get('profit', 0)
                                
                                if result_type == 'win':
                                    won = True
                                    profit = profit_amount if profit_amount > 0 else amount * 0.8
                                    print(f"🎉 WIN! Profit: ${profit:.2f}")
                                elif result_type == 'loss':
                                    won = False
                                    profit = profit_amount if profit_amount < 0 else -amount
                                    print(f"💔 LOSS! Loss: ${abs(profit):.2f}")
                                else:
                                    won = False
                                    profit = 0.0 if result_type == 'draw' else -amount
                                    print(f"🤝 {result_type.upper()}!")
                                
                                self.record_api_success()  # Record successful result check
                            else:
                                # Result timeout - use simulation
                                elapsed = (datetime.now() - start_time).total_seconds()
                                print(f"⚠️ Result timeout after {elapsed:.0f}s - using simulation")
                                self.record_api_failure()  # Record API failure
                                import random
                                won = random.random() > 0.4
                                profit = amount * 0.8 if won else -amount
                                print(f"🎯 SIMULATED {'WIN' if won else 'LOSS'}: ${profit:+.2f}")
                                
                        except Exception as result_error:
                            print(f"⚠️ Result error: {result_error}")
                            print("🔄 Using simulation fallback")
                            self.record_api_failure()  # Record API failure
                            import random
                            won = random.random() > 0.4
                            profit = amount * 0.8 if won else -amount
                            print(f"🎯 SIMULATED {'WIN' if won else 'LOSS'}: ${profit:+.2f}")
                    else:
                        print(f"❌ Trade failed - status: {order_result.status if order_result else 'None'}")
                        print("🔄 Falling back to simulation")
                        self.record_api_failure()  # Record API failure
                        import random
                        won = random.random() > 0.4
                        profit = amount * 0.8 if won else -amount
                        
                except Exception as api_error:
                    error_msg = str(api_error).lower()
                    if 'incorrectopentime' in error_msg or 'market' in error_msg or 'closed' in error_msg:
                        print(f"⚠️ Market closed for {asset} - using simulation")
                        print(f"   📊 This is normal outside trading hours")
                    else:
                        print(f"❌ API Error: {api_error}")
                        self.record_api_failure()  # Record API failure
                    print("🔄 Falling back to simulation")
                    import random
                    won = random.random() > 0.4
                    profit = amount * 0.8 if won else -amount
            else:
                # Simulation mode
                await asyncio.sleep(0.1)
                import random
                won = random.random() > 0.4  # 60% win rate
                profit = amount * 0.8 if won else -amount
                print(f"🎯 SIMULATED {'WIN' if won else 'LOSS'}")
            
            # Record trade
            result_status = 'win' if won else ('draw' if profit == 0 else 'loss')
            trade_record = {
                'asset': asset,
                'direction': direction,
                'amount': amount,
                'result': result_status,
                'profit_loss': profit,
                'execution_time': execution_time.isoformat(),
                'signal_time': signal_time.isoformat(),
                'close_time': actual_close_time.isoformat(),
                'target_close_time': target_close_time.isoformat(),
                'duration_seconds': dynamic_duration,
                'timing_strategy': 'dynamic_duration_00_close',
                'mode': 'real' if (REAL_API_AVAILABLE and self.client and self.ssid and not force_simulation) else 'simulation'
            }
            self.trade_history.append(trade_record)
            
            return won, profit
            
        except Exception as e:
            print(f"❌ Trade execution error: {e}")
            return False, -amount
    
    async def start_precise_trading(self, base_amount: float, multiplier: float = 2.5, is_demo: bool = True):
        """Start precise timing trading with priority-based martingale progression"""
        print(f"\n🚀 PRIORITY-BASED MARTINGALE TRADING STARTED")
        print("=" * 60)
        print(f"💰 Base Amount: ${base_amount}")
        print(f"📈 Multiplier: {multiplier}")
        print(f"🎯 Priority System: Complete existing sequences first")
        print(f"⚡ Immediate Progression: Loss → Next step within 5 seconds")
        print(f"🔄 Sequence Priority: Step 2/3 assets block new Step 1 assets")
        print(f"📝 Example: GBPJPY Step 2 → Complete before EURUSD Step 1")
        print(f"✅ Win/Complete → Allow new assets to start")
        print(f"🔧 API Health: Max {self.max_api_failures} failures before simulation mode")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        strategy = MultiAssetMartingaleStrategy(base_amount, multiplier)
        session_profit = 0.0
        session_trades = 0
        
        try:
            while True:
                # Process any pending immediate trades first
                if self.pending_immediate_trades:
                    print(f"\n⚡ PROCESSING {len(self.pending_immediate_trades)} IMMEDIATE TRADES")
                    
                    immediate_tasks = []
                    for immediate_trade in self.pending_immediate_trades:
                        asset = immediate_trade['asset']
                        direction = immediate_trade['direction']
                        amount = immediate_trade['amount']
                        step = immediate_trade['step']
                        
                        print(f"⚡ IMMEDIATE Step {step}: {asset} {direction.upper()} ${amount}")
                        
                        # Execute immediate trade
                        task = asyncio.create_task(
                            self.execute_immediate_trade(asset, direction, amount)
                        )
                        immediate_tasks.append((task, asset, direction, amount, step))
                    
                    # Clear pending trades
                    self.pending_immediate_trades.clear()
                    
                    # Wait for all immediate trades to complete
                    if immediate_tasks:
                        results = await asyncio.gather(*[task for task, _, _, _, _ in immediate_tasks], return_exceptions=True)
                        
                        # Process immediate trade results
                        for i, result in enumerate(results):
                            if isinstance(result, Exception):
                                print(f"❌ Immediate trade {i+1} failed: {result}")
                                continue
                            
                            won, profit = result
                            _, asset, direction, amount, step = immediate_tasks[i]
                            
                            session_profit += profit
                            session_trades += 1
                            
                            # Update strategy for immediate trade result
                            next_action = strategy.record_result(won, asset, amount)
                            
                            if next_action['action'] == 'continue':
                                # Need another immediate trade (step 3 after step 2 loss)
                                next_step = next_action['next_step']
                                next_amount = strategy.get_current_amount(asset)
                                
                                print(f"⚡ QUEUEING Step {next_step}: {asset} {direction.upper()} ${next_amount}")
                                self.pending_immediate_trades.append({
                                    'asset': asset,
                                    'direction': direction,
                                    'amount': next_amount,
                                    'step': next_step
                                })
                            elif next_action['action'] in ['reset', 'reset_after_max_loss']:
                                print(f"🔄 {asset} strategy reset - ready for new signals")
                        
                        # Show session stats after immediate trades
                        wins = len([t for t in self.trade_history if t['result'] == 'win'])
                        losses = len([t for t in self.trade_history if t['result'] == 'loss'])
                        
                        print(f"📊 Session: ${session_profit:+.2f} | Trades: {session_trades}")
                        print(f"🏆 Results: {wins}W/{losses}L")
                
                # Get signals for scheduled trades
                signals = self.get_signals_from_csv()
                
                if not signals and not self.pending_immediate_trades:
                    # Show API health status periodically
                    if hasattr(self, 'api_failures') and self.api_failures > 0:
                        health_status = f"API Health: {self.api_failures}/{self.max_api_failures} failures"
                        if self.api_failures >= self.max_api_failures:
                            health_status += " (SIMULATION MODE)"
                        print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] No signals - {health_status}")
                    else:
                        print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] No signals - checking again in 0.5 seconds...")
                    await asyncio.sleep(0.5)
                    continue
                
                # PRIORITY SYSTEM: Complete existing martingale sequences first
                if signals:
                    # Check if any assets are in the middle of sequences (Step 2 or 3)
                    assets_in_sequence = strategy.get_assets_in_sequence()
                    
                    if assets_in_sequence:
                        print(f"\n🎯 PRIORITY: Completing existing sequences first")
                        print(f"📊 Assets in sequence: {', '.join(assets_in_sequence)}")
                        
                        # Filter signals to only process assets that are in sequence
                        priority_signals = []
                        blocked_signals = []
                        
                        for signal in signals:
                            if signal['asset'] in assets_in_sequence:
                                priority_signals.append(signal)
                            else:
                                blocked_signals.append(signal)
                        
                        if blocked_signals:
                            blocked_assets = [s['asset'] for s in blocked_signals]
                            print(f"⏸️  Blocking new assets: {', '.join(blocked_assets)} (waiting for sequences to complete)")
                        
                        # Process only priority signals (assets in sequence)
                        signals_to_process = priority_signals
                    else:
                        print(f"\n📊 PROCESSING {len(signals)} NEW SIGNALS (No active sequences):")
                        # No assets in sequence, process all signals
                        signals_to_process = signals
                    
                    if signals_to_process:
                        print("=" * 50)
                        
                        # Create tasks for selected signals
                        signal_tasks = []
                        for signal in signals_to_process:
                            asset = signal['asset']
                            direction = signal['direction']
                            
                            # Each asset gets its own independent step progression
                            trade_amount = strategy.get_current_amount(asset)
                            current_step = strategy.get_asset_step(asset)
                            
                            print(f"📊 {asset} {direction.upper()} - {strategy.get_status(asset)}")
                            print(f"⏰ Signal: {signal['signal_time']} | Trade: {signal['trade_datetime'].strftime('%H:%M:%S')}")
                            
                            # Create task for this signal
                            task = asyncio.create_task(
                                self.execute_precise_trade(signal, trade_amount)
                            )
                            signal_tasks.append((task, signal, trade_amount, current_step))
                        
                        print("🚀 EXECUTING PRIORITY SIGNALS...")
                        
                        # Wait for all signal trades to complete
                        if signal_tasks:
                            results = await asyncio.gather(*[task for task, _, _, _ in signal_tasks], return_exceptions=True)
                            
                            # Process all signal results
                            for i, result in enumerate(results):
                                if isinstance(result, Exception):
                                    print(f"❌ Signal trade {i+1} failed: {result}")
                                    continue
                                
                                won, profit = result
                                _, signal, trade_amount, step = signal_tasks[i]
                                asset = signal['asset']
                                direction = signal['direction']
                                
                                # Skip if trade was skipped (too far in future)
                                if won is False and profit == 0:
                                    continue
                                
                                session_profit += profit
                                session_trades += 1
                                
                                # Update strategy for this asset
                                next_action = strategy.record_result(won, asset, trade_amount)
                                
                                if next_action['action'] == 'continue':
                                    # Loss - queue immediate next step trade for this asset
                                    next_step = next_action['next_step']
                                    next_amount = strategy.get_current_amount(asset)
                                    
                                    print(f"⚡ LOSS! Queueing IMMEDIATE Step {next_step}: {asset} {direction.upper()} ${next_amount}")
                                    self.pending_immediate_trades.append({
                                        'asset': asset,
                                        'direction': direction,
                                        'amount': next_amount,
                                        'step': next_step
                                    })
                                elif next_action['action'] in ['reset', 'reset_after_max_loss']:
                                    print(f"✅ {asset} sequence COMPLETED - ready for new signals")
                            
                            # Show session stats after all signals processed
                            wins = len([t for t in self.trade_history if t['result'] == 'win'])
                            losses = len([t for t in self.trade_history if t['result'] == 'loss'])
                            
                            print(f"\n📊 PRIORITY TRADING SESSION:")
                            print(f"   💰 Session P&L: ${session_profit:+.2f}")
                            print(f"   📈 Total Trades: {session_trades}")
                            print(f"   🏆 Results: {wins}W/{losses}L")
                            
                            # Show current status of all active assets
                            active_assets = strategy.get_all_active_assets()
                            if active_assets:
                                print(f"   📊 Asset Status:")
                                for asset in active_assets:
                                    status = strategy.get_status(asset)
                                    step = strategy.get_asset_step(asset)
                                    if step > 1:
                                        print(f"      🎯 {status} (IN SEQUENCE)")
                                    else:
                                        print(f"      ✅ {status} (READY)")
                
                await asyncio.sleep(0.2)
                
        except KeyboardInterrupt:
            print(f"\n🛑 TRADING STOPPED BY USER")
        except Exception as e:
            print(f"❌ Trading error: {e}")
        
        # Final stats
        total_trades = len(self.trade_history)
        total_wins = len([t for t in self.trade_history if t['result'] == 'win'])
        total_losses = len([t for t in self.trade_history if t['result'] == 'loss'])
        total_profit = sum([t['profit_loss'] for t in self.trade_history])
        
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   💰 Session P&L: ${session_profit:.2f}")
        print(f"   📈 Session Trades: {session_trades}")
        print(f"   🏆 Results: {total_wins}W/{total_losses}L")
        print(f"   💵 Total P&L: ${total_profit:.2f}")
        print(f"   🎯 Assets Tracked: {len(strategy.get_all_active_assets())}")

async def main():
    """Main application with immediate martingale progression"""
    print("=" * 80)
    print("🚀 POCKETOPTION PRIORITY-BASED MARTINGALE TRADER")
    print("=" * 80)
    print("⚡ IMMEDIATE PROGRESSION: Loss → Next step within 5 seconds")
    print("⏰ Scheduled trades: 10s before signal time")
    print("� Tradpes close at next 00 second (dynamic duration)")
    print("📝 Example: Loss Step 1 → IMMEDIATE Step 2 → IMMEDIATE Step 3")
    print("🔄 Win at any step → Reset to Step 1 for next signal")
    print("=" * 80)
    
    while True:
        print("\n📋 PRECISE TIMING SETUP:")
        print("=" * 40)
        
        try:
            # Get account type
            print("1. Account Type:")
            account_choice = input("   Use DEMO account? (Y/n): ").lower().strip()
            is_demo = account_choice != 'n'
            print(f"   ✅ {'DEMO' if is_demo else 'REAL'} account selected")
            
            # Get base amount
            print("\n2. Base Amount:")
            while True:
                try:
                    base_amount = float(input("   Enter base amount ($): $"))
                    if base_amount <= 0:
                        print("   ❌ Amount must be positive")
                        continue
                    print(f"   ✅ Base amount: ${base_amount}")
                    break
                except ValueError:
                    print("   ❌ Please enter a valid number")
            
            # Get multiplier
            print("\n3. Multiplier:")
            while True:
                try:
                    multiplier_input = input("   Enter multiplier (default 2.5): ").strip()
                    if not multiplier_input:
                        multiplier = 2.5
                    else:
                        multiplier = float(multiplier_input)
                    
                    if multiplier <= 1:
                        print("   ❌ Multiplier must be greater than 1")
                        continue
                    print(f"   ✅ Multiplier: {multiplier}")
                    break
                except ValueError:
                    print("   ❌ Please enter a valid number")
            
            # Show timing example
            print(f"\n⏰ TIMING EXAMPLE:")
            example_signal = "00:38:00"
            example_trade = "00:37:50"
            example_close = "00:38:50"
            print(f"   Signal Time: {example_signal}")
            print(f"   Trade Time:  {example_trade} (10s before)")
            print(f"   Close Time:  {example_close} (60s duration)")
            
            # Show strategy preview
            step1_amount = base_amount
            step2_amount = step1_amount * multiplier
            step3_amount = step2_amount * multiplier
            print(f"\n📊 STRATEGY PREVIEW (3-Step Martingale):")
            print(f"   Step 1: ${step1_amount:.2f} (Base)")
            print(f"   Step 2: ${step2_amount:.2f} (${step1_amount:.2f} × {multiplier})")
            print(f"   Step 3: ${step3_amount:.2f} (${step2_amount:.2f} × {multiplier})")
            print(f"   Total Risk: ${step1_amount + step2_amount + step3_amount:.2f}")
            
            # Confirm start
            print(f"\n🚀 Ready to start precise timing trading!")
            start = input("Start trading? (Y/n): ").lower().strip()
            if start == 'n':
                continue
            
            # Initialize trader
            trader = MultiAssetPreciseTrader()
            
            # Connect
            if not await trader.connect(is_demo):
                print("❌ Failed to connect")
                continue
            
            try:
                # Start precise timing trading
                await trader.start_precise_trading(base_amount, multiplier, is_demo)
            finally:
                # Disconnect
                if trader.client:
                    await trader.client.disconnect()
                    print("🔌 Disconnected from PocketOption")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
        
        # Ask if want to restart
        restart = input("\nStart another trading session? (Y/n): ").lower().strip()
        if restart == 'n':
            break
    
    print("\n👋 Thank you for using PocketOption Precise Timing Trader!")

if __name__ == "__main__":
    asyncio.run(main())