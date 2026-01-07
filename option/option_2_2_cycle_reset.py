"""
Option 2 - 2-Cycle Reset Martingale
Extracted from app.py

STRATEGY DESCRIPTION:
- 2 cycles × 3 steps each = up to 6 total trades
- Independent Cycles: Each cycle starts from base amount
- Both cycles start with base amount (reset strategy)
- Win in any step resets to Cycle 1, Step 1
- Loss continues to next step in same cycle
"""

from common_components import *

class Option2TradingStrategy:
    """Option 2: 2-Cycle Reset Martingale Strategy"""
    
    async def _run_supabase_trading_option_2(self, account_type: str):
        """Run Supabase trading with Option 2 (2-Cycle Reset)."""
        print(f"\n🚀 STARTING AUTOMATED SUPABASE TRADING - OPTION 2")
        print(f"💼 Account Type: {account_type.upper()}")
        print("=" * 60)
        
        try:
            # Connect and get account info
            await self._connect_and_show_account_info(account_type)
            
            # Override strategy option to 2
            print("\n🎯 Starting automated trading with 2-Cycle Reset Martingale...")
            await self._buy_supabase_signals_direct(account_type, strategy_option=2)
            
        except KeyboardInterrupt:
            print("\n✅ Trading interrupted by user.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Error in Option 2 trading: {e}")

    def _init_cycle_tracking_option_2(self, config: Dict[str, Any]) -> None:
        """Initialize cycle tracking for Option 2 - 2-Cycle Reset Martingale."""
        # Option 2: 2-Cycle Reset Martingale
        self._global_cycle_tracker = {
            'current_cycle': 1,  # Start at cycle 1
            'current_step': 1,   # Start at step 1
            'config': config
        }
        strategy_name = "2-Cycle Reset"
        
        print(f"\n🔄 Parallel Asset Processing Initialized:")
        print(f"🎯 Strategy: Option 2 - {strategy_name}")
        print(f"📊 Cycles: 2 cycles × 3 steps each = up to 6 total trades")
        print(f"💰 Base Amount: ${config['base_amount']:.2f}")
        print(f"📈 Multiplier: {config['multiplier']}x")
        print(f"🔄 Current Global Cycle: {self._global_cycle_tracker['current_cycle']}")
        print(f"🔄 Current Global Step: {self._global_cycle_tracker['current_step']}")
        print(f"🎯 Asset Processing: Independent parallel processing")
        print(f"⚡ Signal Processing: Immediate execution (no queuing)")
        print(f"🔄 Parallel Processing: All signals processed immediately")
        
        print(f"📊 Independent Cycles: Each cycle starts from base amount")

    async def _execute_option_2_strategy_parallel(self, supabase_client, signal_id: str, asset_name: str, 
                                                  asset: str, direction: str, duration: int,
                                                  tracker: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute Option 2: 2-Cycle Reset Martingale Strategy (Sequential Processing).
        
        Strategy Logic:
        - 2 Cycles maximum
        - Each cycle: 3-step martingale (base, base×multiplier, base×multiplier²)
        - Both cycles start with base amount (independent/reset strategy)
        - Win in any step resets to Cycle 1, Step 1
        - Loss continues to next step in same cycle
        - After 3 losses in a cycle, move to next cycle (or stay in Cycle 2)
        """
        current_cycle = tracker['current_cycle']
        current_step = tracker['current_step']
        config = tracker['config']
        
        print(f"🚀 OPTION 2 STRATEGY CALLED: Signal {signal_id} - {asset} {direction.upper()}")
        print(f"📊 Current state: C{current_cycle}S{current_step}")
        print(f"⚡ Execute steps one by one - continue after LOSS until WIN or max steps")
        
        all_results = []
        
        # Continue martingale until WIN or max steps (3) reached
        while current_step <= 3:
            # Both cycles always start with base amount (independent/reset strategy)
            if current_step == 1:
                starting_amount = config['base_amount']
            else:
                # Continue martingale from previous step
                starting_amount = config['base_amount'] * (config['multiplier'] ** (current_step - 1))
            
            print(f"🔄 Option 2 - C{current_cycle}S{current_step}: ${starting_amount:.2f} | {asset} {direction.upper()} (Reset)")
            print(f"   📊 Cycle {current_cycle} Step {current_step}/3 (Independent Reset Strategy)")
            print(f"   💰 Trade Amount: ${starting_amount:.2f}")
            
            # Calculate timing for this step
            if current_step == 1:
                # First step: execute immediately (already timed 8s before signal)
                execution_delay = 0
            else:
                # Subsequent steps: wait until next :00 with max 1s delay
                execution_delay = await self._calculate_next_minute_delay_max_1s(current_step)
            
            if execution_delay > 0:
                print(f"⏰ Waiting {execution_delay:.1f}s for Step {current_step} (max 1s delay)")
                await asyncio.sleep(execution_delay)
            
            # Execute single trade
            trade_result = await self._execute_single_trade_sequential(
                supabase_client, signal_id, asset_name, asset, direction, 
                starting_amount, 59, config, current_cycle, current_step  # 59s to close at :59
            )
            
            if not trade_result:
                print(f"❌ Step {current_step} failed to execute")
                break
            
            all_results.append(trade_result)
            
            # Process result and update tracker
            print(f"🔍 Option 2 - Trade result: {trade_result['result']} for C{current_cycle}S{current_step}")
            
            if trade_result['result'] == 'win':
                print(f"🎉 WIN C{current_cycle}S{current_step}! → Reset to C1S1 (Option 2)")
                # Reset to Cycle 1, Step 1
                tracker['current_cycle'] = 1
                tracker['current_step'] = 1
                break  # Exit martingale - WIN achieved
                
            elif trade_result['result'] in ['asset_closed', 'trade_failed', 'blocked']:
                print(f"⚠️ {trade_result['result'].upper()} C{current_cycle}S{current_step} - Cannot continue")
                break  # Exit martingale - cannot continue with this asset
                
            else:  # Loss
                print(f"💔 LOSS C{current_cycle}S{current_step} - Continuing martingale progression")
                
                # Move to next step within the same cycle
                if current_step < 3:
                    current_step += 1
                    tracker['current_step'] = current_step
                    next_amount = config['base_amount'] * (config['multiplier'] ** (current_step - 1))
                    print(f"📈 Continuing to C{current_cycle}S{current_step} - Amount: ${next_amount:.2f}")
                    print(f"🔄 Will execute next step in martingale sequence...")
                    continue  # Continue the martingale loop on same signal
                    
                else:
                    # Completed 3 steps in current cycle
                    if current_cycle < 2:
                        # Move to Cycle 2
                        tracker['current_cycle'] = 2
                        tracker['current_step'] = 1
                        next_amount = config['base_amount']  # Reset amount for Cycle 2
                        print(f"🔄 Moving to Cycle 2, Step 1 - Amount: ${next_amount:.2f} (RESET)")
                        print(f"   💡 Cycle 2: Independent reset - starts with base amount")
                        
                    else:
                        # Already in Cycle 2, completed all steps - stay in Cycle 2, Step 1
                        tracker['current_step'] = 1
                        next_amount = config['base_amount']
                        print(f"🔄 Cycle 2 complete - Staying in C2S1 - Amount: ${next_amount:.2f} (RESET)")
                        print(f"   💡 Cycle 2 continues: Independent reset strategy")
                    
                    break  # Exit this signal's martingale - completed all steps in cycle
        
        return all_results

    async def _calculate_next_minute_delay_max_1s(self, step: int) -> float:
        """Calculate delay to next minute with maximum 1 second delay for Option 2."""
        current_time = datetime.now()
        current_second = current_time.second
        
        # For steps 2 and 3, wait until next :00 but with max 1s delay
        if step > 1:
            if current_second <= 1:
                # Already at :00 or :01, execute immediately
                return 0
            else:
                # Wait until next minute, but cap at 1 second
                seconds_to_next_minute = 60 - current_second
                return min(seconds_to_next_minute, 1.0)
        
        return 0  # Step 1 executes immediately

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