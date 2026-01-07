"""
Option 5 - 3-Cycle Continuous Martingale
Extracted from app.py

STRATEGY DESCRIPTION:
- 3 cycles × 3 steps each = 9 total trades maximum
- 3-Cycle Continuous Martingale: 3 cycles × 3 steps = 9 total trades
- Each signal executes complete 3-step cycle at current global cycle level
- Pure continuous progression across all cycles

CONTINUOUS MARTINGALE PROGRESSION ($1 Base, 2.5x multiplier):
Cycle 1: Trade #1($1.00) → Trade #2($2.50) → Trade #3($6.25)
Cycle 2: Trade #4($15.63) → Trade #5($39.06) → Trade #6($97.66)
Cycle 3: Trade #7($244.15) → Trade #8($610.38) → Trade #9($1,525.94)
"""

from common_components import *

class Option5TradingStrategy:
    """Option 5: 3-Cycle Continuous Martingale Strategy"""
    
    async def _run_supabase_trading_option_5(self, account_type: str):
        """Run Supabase trading with Option 5 (3-Cycle Continuous Martingale)."""
        print(f"\n🚀 STARTING AUTOMATED SUPABASE TRADING - OPTION 5")
        print(f"💼 Account Type: {account_type.upper()}")
        print("=" * 60)
        
        try:
            # Connect and get account info
            await self._connect_and_show_account_info(account_type)
            
            # Override strategy option to 5
            print("\n🎯 Starting automated trading with 3-Cycle Continuous Martingale...")
            await self._buy_supabase_signals_direct(account_type, strategy_option=5)
            
        except KeyboardInterrupt:
            print("\n✅ Trading interrupted by user.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Error in Option 5 trading: {e}")

    def _init_cycle_tracking_option_5(self, config: Dict[str, Any]) -> None:
        """Initialize cycle tracking for Option 5 - 3-Cycle Continuous Martingale."""
        # Option 5: 3-Cycle Continuous Martingale (Using Option 1 Concept)
        self._global_cycle_tracker = {
            'current_cycle': 1,  # Start at cycle 1
            'current_step': 1,   # Start at step 1
            'continuous_trade_number': 1,  # Track continuous trade number (1-9)
            'cycle_2_last_amount': config['base_amount'],  # Track progression
            'config': config
        }
        strategy_name = "3-Cycle Continuous Martingale"
        
        print(f"\n🔄 Parallel Asset Processing Initialized:")
        print(f"🎯 Strategy: Option 5 - {strategy_name}")
        print(f"📊 Cycles: 3 cycles × 3 steps each = up to 9 total trades")
        print(f"💰 Base Amount: ${config['base_amount']:.2f}")
        print(f"📈 Multiplier: {config['multiplier']}x")
        print(f"🔄 Current Global Cycle: {self._global_cycle_tracker['current_cycle']}")
        print(f"🔄 Current Global Step: {self._global_cycle_tracker['current_step']}")
        print(f"📊 Continuous Trade Number: {self._global_cycle_tracker['continuous_trade_number']}")
        print(f"🎯 Asset Processing: Independent parallel processing")
        print(f"⚡ Signal Processing: Immediate execution (no queuing)")
        print(f"🔄 Parallel Processing: All signals processed immediately")
        
        print(f"📊 3-Cycle Continuous Martingale: 3 cycles × 3 steps = 9 total trades")
        print(f"🔧 Each signal executes complete 3-step cycle at current global cycle level")
        
        # Show the complete progression
        print(f"\n📋 CONTINUOUS MARTINGALE PROGRESSION:")
        print(f"   Cycle 1: Trade #1(${config['base_amount']:.2f}) → Trade #2(${config['base_amount'] * config['multiplier']:.2f}) → Trade #3(${config['base_amount'] * (config['multiplier'] ** 2):.2f})")
        print(f"   Cycle 2: Trade #4(${config['base_amount'] * (config['multiplier'] ** 3):.2f}) → Trade #5(${config['base_amount'] * (config['multiplier'] ** 4):.2f}) → Trade #6(${config['base_amount'] * (config['multiplier'] ** 5):.2f})")
        print(f"   Cycle 3: Trade #7(${config['base_amount'] * (config['multiplier'] ** 6):.2f}) → Trade #8(${config['base_amount'] * (config['multiplier'] ** 7):.2f}) → Trade #9(${config['base_amount'] * (config['multiplier'] ** 8):.2f})")

    async def _execute_option_5_strategy_parallel(self, supabase_client, signal_id: str, asset_name: str, 
                                                  asset: str, direction: str, duration: int,
                                                  tracker: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute Option 5: 3-Cycle Continuous Martingale Strategy (3-Step Cycles).
        
        OPTION 5 CONCEPT:
        - 3 Cycles, each with 3 steps (9 total trades maximum)
        - Continuous martingale progression across all cycles
        - Each signal executes complete 3-step cycle at current global cycle level
        
        Cycle 1 - 3-Step Martingale ($1 Base, 2.5x multiplier):
        Trade #1: $1.00 (Base)
        Trade #2: $2.50 (1 × 2.5)  
        Trade #3: $6.25 (2.5 × 2.5)
        
        Cycle 2 - Continuing Martingale from Cycle 1:
        Trade #4: $15.63 (6.25 × 2.5)
        Trade #5: $39.06 (15.63 × 2.5)
        Trade #6: $97.66 (39.06 × 2.5)
        
        Cycle 3 - Continuing Martingale from Cycle 2:
        Trade #7: $244.15 (97.66 × 2.5)
        Trade #8: $610.38 (244.15 × 2.5)
        Trade #9: $1,525.94 (610.38 × 2.5)
        
        - Win in any step resets global state to Cycle 1
        - Loss in all 3 steps of a cycle advances global cycle for next signals
        """
        # Get current global cycle state (what cycle new signals should start at)
        global_cycle = tracker['current_cycle']
        config = tracker['config']
        
        # Display current global state (like Option 1)
        print(f"🔄 Signal {signal_id}: Starting C{global_cycle} continuous martingale for {asset} {direction.upper()}")
        print(f"📊 GLOBAL STATE: Currently at Cycle {global_cycle} (New signals start here)")
        
        # Show what this cycle contains
        if global_cycle == 1:
            print(f"📋 CYCLE 1 SEQUENCE: Trade #1(${config['base_amount']:.2f}) → Trade #2(${config['base_amount'] * config['multiplier']:.2f}) → Trade #3(${config['base_amount'] * (config['multiplier'] ** 2):.2f})")
        elif global_cycle == 2:
            print(f"📋 CYCLE 2 SEQUENCE: Trade #4(${config['base_amount'] * (config['multiplier'] ** 3):.2f}) → Trade #5(${config['base_amount'] * (config['multiplier'] ** 4):.2f}) → Trade #6(${config['base_amount'] * (config['multiplier'] ** 5):.2f})")
        else:
            print(f"📋 CYCLE 3 SEQUENCE: Trade #7(${config['base_amount'] * (config['multiplier'] ** 6):.2f}) → Trade #8(${config['base_amount'] * (config['multiplier'] ** 7):.2f}) → Trade #9(${config['base_amount'] * (config['multiplier'] ** 8):.2f})")
        
        # Execute complete 3-step cycle for this signal
        all_results = []
        current_step = 1  # Always start at step 1 for each signal
        
        # Continue martingale until win or max steps (3) reached
        while current_step <= 3:
            # Calculate continuous trade number based on global cycle and current step
            if global_cycle == 1:
                # Cycle 1: Trades 1, 2, 3
                continuous_trade_number = current_step
            elif global_cycle == 2:
                # Cycle 2: Trades 4, 5, 6
                continuous_trade_number = 3 + current_step
            else:
                # Cycle 3: Trades 7, 8, 9
                continuous_trade_number = 6 + current_step
            
            # Calculate amount based on continuous trade number (pure continuous martingale)
            starting_amount = config['base_amount'] * (config['multiplier'] ** (continuous_trade_number - 1))
            
            # Display current step with detailed information (like Option 1)
            print(f"🔄 C{global_cycle}S{current_step}: ${starting_amount:.2f} | {asset} {direction.upper()}")
            print(f"   📊 ACTIVE: Cycle {global_cycle}, Step {current_step} of 3 (Trade #{continuous_trade_number} of 9)")
            print(f"   💰 Amount: ${config['base_amount']:.2f} × {config['multiplier']}^{continuous_trade_number-1} = ${starting_amount:.2f}")
            print(f"   🎯 This Step: {'WIN resets to C1S1' if current_step < 3 else 'WIN resets to C1S1 | LOSS advances cycle'}")
            
            # Calculate timing for this step
            if current_step == 1:
                # First step: execute immediately (already timed 8s before signal)
                execution_delay = 0
            else:
                # Subsequent steps: wait until next :00 with max 1s delay
                execution_delay = await self._calculate_next_minute_delay_max_1s(current_step)
            
            if execution_delay > 0:
                print(f"⏰ Waiting {execution_delay:.1f}s for C{global_cycle}S{current_step} (max 1s delay)")
                await asyncio.sleep(execution_delay)
            
            # Execute single trade and WAIT for result (sequential execution)
            trade_result = await self._execute_single_trade_sequential(
                supabase_client, signal_id, asset_name, asset, direction, 
                starting_amount, 59, config, global_cycle, current_step  # 59s to close at :59
            )
            
            if not trade_result:
                print(f"❌ C{global_cycle}S{current_step} failed to execute")
                break
                
            all_results.append(trade_result)
            
            # Add continuous trade number to result for tracking
            trade_result['continuous_trade_number'] = continuous_trade_number
            
            # Process result with detailed state information (like Option 1)
            if trade_result['result'] == 'win':
                print(f"🎉 WIN C{global_cycle}S{current_step} (Trade #{continuous_trade_number})! → Global reset to C1")
                print(f"✅ GLOBAL STATE CHANGE: C{global_cycle} → C1 (All future signals start at Cycle 1)")
                # Reset global cycle to 1 for next signals
                tracker['current_cycle'] = 1
                tracker['current_step'] = 1
                tracker['continuous_trade_number'] = 1
                # Reset cycle progression tracking
                tracker['cycle_2_last_amount'] = config['base_amount']
                print(f"🔄 Next signals will start at C1S1 (Trade #1) - ${config['base_amount']:.2f}")
                break  # Exit martingale sequence - signal completed successfully
                
            elif trade_result['result'] in ['asset_closed', 'trade_failed', 'blocked']:
                print(f"⚠️ {trade_result['result'].upper()} C{global_cycle}S{current_step} (Trade #{continuous_trade_number}) - Ending sequence")
                print(f"📊 GLOBAL STATE: Remains at C{global_cycle} (No change)")
                break  # Exit martingale sequence - cannot continue with this asset
                
            else:  # LOSS
                print(f"💔 LOSS C{global_cycle}S{current_step} (Trade #{continuous_trade_number})")
                
                if current_step < 3:
                    # Continue to next step immediately in SAME cycle (like Option 1)
                    current_step += 1
                    next_continuous_trade = continuous_trade_number + 1
                    next_amount = config['base_amount'] * (config['multiplier'] ** (next_continuous_trade - 1))
                    print(f"📈 Continuing martingale on same asset → C{global_cycle}S{current_step}")
                    print(f"🔄 NEXT STEP: C{global_cycle}S{current_step} (Trade #{next_continuous_trade}) - ${next_amount:.2f}")
                    # NO DELAY - Start next step immediately
                    continue  # Continue the martingale loop in same cycle
                else:
                    # Completed 3 steps with all losses - update global cycle for next signals (like Option 1)
                    print(f"💔 All 3 steps lost in C{global_cycle} (Trades {continuous_trade_number-2}-{continuous_trade_number})")
                    
                    if global_cycle < 3:
                        # Move global cycle up for next signals
                        old_cycle = global_cycle
                        tracker['current_cycle'] = global_cycle + 1
                        tracker['current_step'] = 1
                        
                        # Store the last amount from this cycle for continuous progression
                        tracker['cycle_2_last_amount'] = starting_amount
                        print(f"📊 Stored last amount: ${tracker['cycle_2_last_amount']:.2f} for continuous progression")
                        
                        # Calculate what the next signal will start with
                        next_cycle = tracker['current_cycle']
                        if next_cycle == 2:
                            next_start_trade = 4
                            next_start_amount = config['base_amount'] * (config['multiplier'] ** 3)
                            print(f"✅ GLOBAL STATE CHANGE: C{old_cycle} → C2")
                            print(f"🔄 Next signals will start at C2S1 (Trade #4) - ${next_start_amount:.2f}")
                            print(f"📋 NEXT CYCLE SEQUENCE: Trade #4(${config['base_amount'] * (config['multiplier'] ** 3):.2f}) → Trade #5(${config['base_amount'] * (config['multiplier'] ** 4):.2f}) → Trade #6(${config['base_amount'] * (config['multiplier'] ** 5):.2f})")
                        else:  # next_cycle == 3
                            next_start_trade = 7
                            next_start_amount = config['base_amount'] * (config['multiplier'] ** 6)
                            print(f"✅ GLOBAL STATE CHANGE: C{old_cycle} → C3")
                            print(f"🔄 Next signals will start at C3S1 (Trade #7) - ${next_start_amount:.2f}")
                            print(f"📋 NEXT CYCLE SEQUENCE: Trade #7(${config['base_amount'] * (config['multiplier'] ** 6):.2f}) → Trade #8(${config['base_amount'] * (config['multiplier'] ** 7):.2f}) → Trade #9(${config['base_amount'] * (config['multiplier'] ** 8):.2f})")
                    else:
                        # Stay in Cycle 3 for next signals (maximum reached)
                        tracker['cycle_2_last_amount'] = starting_amount
                        print(f"📊 GLOBAL STATE: Remains at C3 (Maximum cycle reached)")
                        print(f"🔄 Next signals continue at C3S1 (Trade #7) - ${config['base_amount'] * (config['multiplier'] ** 6):.2f}")
                        print(f"📋 CYCLE 3 SEQUENCE: Trade #7(${config['base_amount'] * (config['multiplier'] ** 6):.2f}) → Trade #8(${config['base_amount'] * (config['multiplier'] ** 7):.2f}) → Trade #9(${config['base_amount'] * (config['multiplier'] ** 8):.2f})")
                    
                    # Update continuous trade number for next signals
                    if tracker['current_cycle'] == 1:
                        tracker['continuous_trade_number'] = 1
                    elif tracker['current_cycle'] == 2:
                        tracker['continuous_trade_number'] = 4
                    else:
                        tracker['continuous_trade_number'] = 7
                    
                    break  # Exit this sequence - cycle completed with loss
        
        return all_results

    async def _calculate_next_minute_delay_max_1s(self, step: int) -> float:
        """Calculate delay to next minute with maximum 1 second delay for Option 5."""
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