"""
Option 1 - 3-Cycle Cumulative Martingale
Extracted from app.py

STRATEGY DESCRIPTION:
- 3 cycles × 3 steps each = up to 9 total trades
- Each cycle builds upon the previous cycle's final amount
- Cycle 3 Enhancement: (Cycle 2 last amount) × multiplier
- Global cycle tracking for parallel asset processing
"""

from common_components import *

class Option1TradingStrategy:
    """Option 1: 3-Cycle Cumulative Martingale Strategy"""
    
    async def _run_supabase_trading_option_1(self, account_type: str):
        """Run Supabase trading with Option 1 (3-Cycle Cumulative)."""
        print(f"\n🚀 STARTING AUTOMATED SUPABASE TRADING - OPTION 1")
        print(f"💼 Account Type: {account_type.upper()}")
        print("=" * 60)
        
        try:
            # Connect and get account info
            await self._connect_and_show_account_info(account_type)
            
            # Override strategy option to 1
            print("\n🎯 Starting automated trading with 3-Cycle Cumulative Martingale...")
            await self._buy_supabase_signals_direct(account_type, strategy_option=1)
            
        except KeyboardInterrupt:
            print("\n✅ Trading interrupted by user.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Error in Option 1 trading: {e}")

    def _init_cycle_tracking_option_1(self, config: Dict[str, Any]) -> None:
        """Initialize cycle tracking for Option 1 - 3-Cycle Cumulative Martingale."""
        # Option 1: 3-Cycle Cumulative Martingale
        self._global_cycle_tracker = {
            'current_cycle': 1,  # Start at cycle 1
            'cycle_2_last_amount': config['base_amount'],  # Track Cycle 2 final amount
            'config': config
        }
        strategy_name = "3-Cycle Cumulative"
        
        print(f"\n🔄 Parallel Asset Processing Initialized:")
        print(f"🎯 Strategy: Option 1 - {strategy_name}")
        print(f"📊 Cycles: 3 cycles × 3 steps each = up to 9 total trades")
        print(f"💰 Base Amount: ${config['base_amount']:.2f}")
        print(f"📈 Multiplier: {config['multiplier']}x")
        print(f"🔄 Current Global Cycle: {self._global_cycle_tracker['current_cycle']}")
        print(f"📊 Cycle 2 Last Amount: ${self._global_cycle_tracker['cycle_2_last_amount']:.2f}")
        print(f"🎯 Asset Processing: Independent parallel processing")
        print(f"⚡ Signal Processing: Immediate execution (no queuing)")
        print(f"🔄 Parallel Processing: All signals processed immediately")
        
        print(f"📊 Cycle 3 Enhancement: (Cycle 2 last amount) × {config['multiplier']}")

    async def _execute_option_1_strategy_parallel(self, supabase_client, signal_id: str, asset_name: str, 
                                                  asset: str, direction: str, duration: int, 
                                                  tracker: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute Option 1: 3-Cycle Cumulative Martingale Strategy (Parallel Processing).
        
        Each signal executes a complete 3-step martingale on the same asset.
        Global cycle state determines starting cycle for new signals.
        """
        # Get current global cycle state (what cycle new signals should start at)
        global_cycle = tracker['current_cycle']
        config = tracker['config']
        
        print(f"🔄 Signal {signal_id}: Starting C{global_cycle} martingale for {asset} {direction.upper()}")
        
        # Execute complete 3-step martingale sequence for this signal
        all_results = []
        current_step = 1  # Always start at step 1 for each signal
        
        # Continue martingale until win or max steps (3) reached
        while current_step <= 3:
            # Determine starting amount based on global cycle and current step
            if global_cycle == 1 or global_cycle == 2:
                # Cycle 1 and 2: Start with base amount, continue with martingale
                if current_step == 1:
                    starting_amount = config['base_amount']
                else:
                    # Continue martingale from previous step
                    starting_amount = config['base_amount'] * (config['multiplier'] ** (current_step - 1))
            else:
                # Cycle 3: Start with enhanced amount from Cycle 2
                if current_step == 1:
                    starting_amount = tracker['cycle_2_last_amount'] * config['multiplier']
                else:
                    # Continue martingale from Cycle 3 base
                    cycle_3_base = tracker['cycle_2_last_amount'] * config['multiplier']
                    starting_amount = cycle_3_base * (config['multiplier'] ** (current_step - 1))
            
            print(f"🔄 C{global_cycle}S{current_step}: ${starting_amount:.2f} | {asset} {direction.upper()}")
            
            # Execute single trade
            trade_result = await self._execute_single_trade_parallel(
                supabase_client, signal_id, asset_name, asset, direction, 
                starting_amount, duration, config, global_cycle, current_step
            )
            
            if not trade_result:
                break
                
            all_results.append(trade_result)
            
            # Process result
            if trade_result['result'] == 'win':
                print(f"🎉 WIN C{global_cycle}S{current_step}! → Global reset to C1")
                # Reset global cycle to 1 for next signals
                tracker['current_cycle'] = 1
                tracker['cycle_2_last_amount'] = config['base_amount']
                break  # Exit martingale sequence - signal completed successfully
                
            elif trade_result['result'] in ['asset_closed', 'trade_failed']:
                print(f"⚠️ {trade_result['result'].upper()} C{global_cycle}S{current_step} - Ending sequence")
                break  # Exit martingale sequence - cannot continue with this asset
                
            else:  # LOSS
                print(f"💔 LOSS C{global_cycle}S{current_step}")
                
                if current_step < 3:
                    # Continue to next step immediately on SAME asset (NO WAITING)
                    current_step += 1
                    print(f"📈 Continuing martingale on same asset → C{global_cycle}S{current_step}")
                    # NO DELAY - Start next step immediately
                    continue  # Continue the martingale loop on same asset
                else:
                    # Completed 3 steps with all losses - update global cycle for next signals
                    print(f"💔 All 3 steps lost on {asset}")
                    
                    if global_cycle < 3:
                        # Move global cycle up for next signals
                        tracker['current_cycle'] = global_cycle + 1
                        
                        # Store Cycle 2 last amount for Cycle 3
                        if global_cycle == 2:
                            tracker['cycle_2_last_amount'] = starting_amount
                            print(f"📊 Stored C2 last: ${tracker['cycle_2_last_amount']:.2f}")
                        
                        print(f"🔄 Next signals will start at C{tracker['current_cycle']}")
                    else:
                        # Stay in Cycle 3 for next signals
                        tracker['cycle_2_last_amount'] = starting_amount  # Update base for next Cycle 3
                        print(f"🔄 Next signals continue at C3")
                    
                    break  # Exit this sequence - signal completed with loss
        
        return all_results

    async def _execute_fast_martingale_strategy(self, supabase_client, signal_id: str, asset_name: str, 
                                              asset: str, direction: str, duration: int, 
                                              tracker: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute SEQUENTIAL Martingale Strategy - Execute steps one by one after losses."""
        global_cycle = tracker['current_cycle']
        config = tracker['config']
        
        print(f"🚀 SEQUENTIAL MARTINGALE: Signal {signal_id} - {asset} {direction.upper()}")
        print(f"⚡ Execute steps one by one - only continue after LOSS")
        
        all_results = []
        current_step = 1
        
        # Continue martingale until WIN or max steps (3) reached
        while current_step <= 3:
            # Calculate amount for current step
            if global_cycle == 1 or global_cycle == 2:
                # Cycle 1 and 2: Standard martingale progression
                if current_step == 1:
                    starting_amount = config['base_amount']
                else:
                    starting_amount = config['base_amount'] * (config['multiplier'] ** (current_step - 1))
            else:
                # Cycle 3: Enhanced progression from Cycle 2
                if current_step == 1:
                    starting_amount = tracker['cycle_2_last_amount'] * config['multiplier']
                else:
                    cycle_3_base = tracker['cycle_2_last_amount'] * config['multiplier']
                    starting_amount = cycle_3_base * (config['multiplier'] ** (current_step - 1))
            
            print(f"🔄 C{global_cycle}S{current_step}: ${starting_amount:.2f} | {asset} {direction.upper()}")
            
            # Execute single trade with minimal delay
            trade_result = await self._execute_single_trade_sequential(
                supabase_client, signal_id, asset_name, asset, direction, 
                starting_amount, duration, config, global_cycle, current_step
            )
            
            if not trade_result:
                print(f"❌ Trade execution failed for C{global_cycle}S{current_step}")
                break
                
            all_results.append(trade_result)
            
            # Process result
            if trade_result['result'] == 'win':
                print(f"🎉 WIN C{global_cycle}S{current_step}! Sequence complete")
                # Reset global cycle to 1 for next signals
                tracker['current_cycle'] = 1
                tracker['cycle_2_last_amount'] = config['base_amount']
                break  # Exit martingale sequence - signal completed successfully
                
            elif trade_result['result'] in ['asset_closed', 'trade_failed']:
                print(f"⚠️ {trade_result['result'].upper()} C{global_cycle}S{current_step} - Cannot continue")
                break  # Exit martingale sequence - cannot continue with this asset
                
            else:  # LOSS
                print(f"💔 LOSS C{global_cycle}S{current_step}")
                
                if current_step < 3:
                    # Continue to next step with minimal delay
                    current_step += 1
                    print(f"📈 Continuing to C{global_cycle}S{current_step} after 1s delay...")
                    await asyncio.sleep(1.0)  # Minimal 1-second delay between steps
                    continue
                else:
                    # Completed 3 steps with all losses
                    print(f"💔 All 3 steps lost on {asset}")
                    
                    if global_cycle < 3:
                        # Move global cycle up for next signals
                        tracker['current_cycle'] = global_cycle + 1
                        
                        # Store Cycle 2 last amount for Cycle 3
                        if global_cycle == 2:
                            tracker['cycle_2_last_amount'] = starting_amount
                            print(f"📊 Stored C2 last: ${tracker['cycle_2_last_amount']:.2f}")
                        
                        print(f"🔄 Next signals will start at C{tracker['current_cycle']}")
                    else:
                        # Stay in Cycle 3 for next signals
                        tracker['cycle_2_last_amount'] = starting_amount
                        print(f"🔄 Next signals continue at C3")
                    
                    break  # Exit this sequence - signal completed with loss
        
        return all_results

    async def _execute_single_trade_parallel(self, supabase_client, signal_id: str, asset_name: str, 
                                           asset: str, direction: str, amount: float, duration: int,
                                           config: Dict[str, Any], cycle: int, step: int) -> Optional[Dict[str, Any]]:
        """Execute a single trade with parallel processing optimizations."""
        try:
            # Check if asset is available
            asset_available, asset_data = await self._safe_asset_check(asset_name, force_open=True)
            
            if not asset_available or not asset_data or len(asset_data) < 3 or not asset_data[2]:
                print(f"❌ C{cycle}S{step}: Asset {asset} is closed")
                return {
                    'signal_id': signal_id,
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'asset_closed',
                    'profit_loss': 0,
                    'timestamp': time.time()
                }
            
            # Execute trade
            print(f"🚀 C{cycle}S{step}: Executing ${amount:.2f} {asset} {direction.upper()}")
            
            status, buy_info = await self._safe_trade_execution(amount, asset_name, direction, duration)
            
            if not status:
                print(f"❌ C{cycle}S{step}: Trade execution failed - {buy_info}")
                return {
                    'signal_id': signal_id,
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'trade_failed',
                    'profit_loss': 0,
                    'timestamp': time.time()
                }
            
            trade_id = buy_info.get('id', 'N/A')
            print(f"✅ C{cycle}S{step}: Trade placed - ID: {trade_id}")
            
            # Wait for trade duration + buffer
            wait_time = duration + 5  # 5 second buffer
            print(f"⏳ C{cycle}S{step}: Waiting {wait_time}s for result...")
            await asyncio.sleep(wait_time)
            
            # Check result
            if await self._safe_win_check(trade_id):
                profit = self.client.get_profit()
                print(f"🎉 C{cycle}S{step}: WIN! Profit: ${profit:.2f}")
                return {
                    'signal_id': signal_id,
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'win',
                    'profit_loss': profit,
                    'trade_id': trade_id,
                    'timestamp': time.time()
                }
            else:
                loss = amount  # Loss is the amount invested
                print(f"💔 C{cycle}S{step}: LOSS - ${loss:.2f}")
                return {
                    'signal_id': signal_id,
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'loss',
                    'profit_loss': -loss,
                    'trade_id': trade_id,
                    'timestamp': time.time()
                }
                
        except Exception as e:
            print(f"❌ C{cycle}S{step}: Error executing trade - {e}")
            logger.error(f"Error in single trade execution: {e}")
            return {
                'signal_id': signal_id,
                'asset': asset,
                'direction': direction,
                'amount': amount,
                'cycle': cycle,
                'step': step,
                'result': 'error',
                'profit_loss': 0,
                'error': str(e),
                'timestamp': time.time()
            }

    async def _execute_single_trade_sequential(self, supabase_client, signal_id: str, asset_name: str, 
                                             asset: str, direction: str, amount: float, duration: int,
                                             config: Dict[str, Any], cycle: int, step: int) -> Optional[Dict[str, Any]]:
        """Execute a single trade with sequential processing (minimal delays)."""
        try:
            # Check if asset is available
            asset_available, asset_data = await self._safe_asset_check(asset_name, force_open=True)
            
            if not asset_available or not asset_data or len(asset_data) < 3 or not asset_data[2]:
                print(f"❌ C{cycle}S{step}: Asset {asset} is closed")
                return {
                    'signal_id': signal_id,
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'asset_closed',
                    'profit_loss': 0,
                    'timestamp': time.time()
                }
            
            # Execute trade
            print(f"🚀 C{cycle}S{step}: Executing ${amount:.2f} {asset} {direction.upper()}")
            
            status, buy_info = await self._safe_trade_execution(amount, asset_name, direction, duration)
            
            if not status:
                print(f"❌ C{cycle}S{step}: Trade execution failed - {buy_info}")
                return {
                    'signal_id': signal_id,
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'trade_failed',
                    'profit_loss': 0,
                    'timestamp': time.time()
                }
            
            trade_id = buy_info.get('id', 'N/A')
            print(f"✅ C{cycle}S{step}: Trade placed - ID: {trade_id}")
            
            # Wait for trade duration + minimal buffer
            wait_time = duration + 2  # Minimal 2 second buffer for sequential
            print(f"⏳ C{cycle}S{step}: Waiting {wait_time}s for result...")
            await asyncio.sleep(wait_time)
            
            # Check result
            if await self._safe_win_check(trade_id):
                profit = self.client.get_profit()
                print(f"🎉 C{cycle}S{step}: WIN! Profit: ${profit:.2f}")
                return {
                    'signal_id': signal_id,
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'win',
                    'profit_loss': profit,
                    'trade_id': trade_id,
                    'timestamp': time.time()
                }
            else:
                loss = amount  # Loss is the amount invested
                print(f"💔 C{cycle}S{step}: LOSS - ${loss:.2f}")
                return {
                    'signal_id': signal_id,
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'loss',
                    'profit_loss': -loss,
                    'trade_id': trade_id,
                    'timestamp': time.time()
                }
                
        except Exception as e:
            print(f"❌ C{cycle}S{step}: Error executing trade - {e}")
            logger.error(f"Error in single trade execution: {e}")
            return {
                'signal_id': signal_id,
                'asset': asset,
                'direction': direction,
                'amount': amount,
                'cycle': cycle,
                'step': step,
                'result': 'error',
                'profit_loss': 0,
                'error': str(e),
                'timestamp': time.time()
            }