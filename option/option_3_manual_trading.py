"""
Option 3 - Manual Trading
Extracted from app.py

STRATEGY DESCRIPTION:
- Manual martingale trading with user-provided asset and direction
- 2 cycles × 2 steps each = up to 4 total trades
- User provides asset and direction manually for each cycle
- Interactive configuration for each trading sequence
"""

from common_components import *

class Option3ManualTrading:
    """Option 3: Manual Trading Strategy"""
    
    async def _run_manual_martingale_trading(self, account_type: str):
        """Run manual martingale trading with user-provided asset and direction."""
        print(f"\n📝 MANUAL MARTINGALE TRADING - 2-CYCLE")
        print(f"💼 Account Type: {account_type.upper()}")
        print("=" * 60)
        
        try:
            # Connect and get account info
            await self._connect_and_show_account_info(account_type)
            
            # Keep running manual trading until user chooses to exit
            while True:
                # Get manual trading configuration
                config = self._get_manual_trading_config()
                if not config:
                    print("❌ Manual trading cancelled by user.")
                    break
                
                print("\n🎯 Starting manual martingale trading...")
                
                # Execute one martingale sequence
                sequence_won = await self._execute_manual_martingale_trading(config)
                
                # After sequence completion, handle next action
                if sequence_won:
                    print(f"\n🎉 Martingale sequence WON! Strategy resets to base amount.")
                    print("=" * 60)
                    print("🔄 Starting new martingale sequence...")
                    # Continue the loop to get new inputs automatically
                    continue
                else:
                    print(f"\n💔 Martingale sequence FAILED! All cycles completed with losses.")
                    print("=" * 60)
                    
                    while True:
                        try:
                            next_action = input("Choose next action:\n1. 🔄 Try again with new inputs\n2. 🏠 Return to main menu\nEnter choice (1/2): ").strip()
                            
                            if next_action == "1":
                                print("\n🔄 Trying again with new inputs...")
                                break  # Continue the outer while loop for new sequence
                            elif next_action == "2":
                                print("🏠 Returning to main menu...")
                                return  # Exit manual trading
                            else:
                                print("❌ Please enter 1 or 2")
                        except KeyboardInterrupt:
                            print("\n🏠 Returning to main menu...")
                            return
            
        except KeyboardInterrupt:
            print("\n✅ Manual trading interrupted by user.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.error(f"Error in manual trading: {e}")

    def _get_manual_trading_config(self) -> Optional[Dict[str, Any]]:
        """Get manual trading configuration from user input."""
        try:
            print("\n" + "=" * 60)
            print("⚙️  MANUAL TRADING CONFIGURATION")
            print("=" * 60)
            
            # Get base amount
            while True:
                try:
                    base_amount = float(input("💰 Enter base trading amount ($): "))
                    if base_amount > 0:
                        break
                    else:
                        print("❌ Amount must be greater than 0")
                except ValueError:
                    print("❌ Please enter a valid number")
            
            # Get multiplier
            while True:
                try:
                    multiplier = float(input("📈 Enter multiplier for martingale (e.g., 2.5): "))
                    if multiplier > 1:
                        break
                    else:
                        print("❌ Multiplier must be greater than 1")
                except ValueError:
                    print("❌ Please enter a valid number")
            
            # Get asset name
            print("\n📊 ASSET SELECTION")
            print("=" * 40)
            print("Common assets:")
            print("• EURUSD_otc, GBPUSD_otc, USDJPY_otc")
            print("• EURJPY_otc, GBPJPY_otc, AUDUSD_otc")
            print("• USDCAD_otc, NZDUSD_otc, EURGBP_otc")
            print("=" * 40)
            
            asset = input("Enter asset name (e.g., EURUSD_otc): ").strip()
            if not asset:
                print("❌ Asset name cannot be empty")
                return None
            
            # Get direction
            print("\n📈 DIRECTION SELECTION")
            print("=" * 40)
            while True:
                direction = input("Enter direction (call/put): ").strip().lower()
                if direction in ['call', 'put']:
                    break
                else:
                    print("❌ Please enter 'call' or 'put'")
            
            # Get timeframe
            print("\n⏰ TIMEFRAME SELECTION")
            print("=" * 40)
            print("Enter timeframe in minutes (integer only):")
            print("• 1 (1 minute)")
            print("• 5 (5 minutes)")
            print("• 15 (15 minutes)")
            print("• 30 (30 minutes)")
            print("=" * 40)
            
            while True:
                try:
                    timeframe_minutes = int(input("Enter timeframe (1, 5, 15, or 30): "))
                    if timeframe_minutes in [1, 5, 15, 30]:
                        duration = timeframe_minutes * 60  # Convert to seconds
                        timeframe = f"{timeframe_minutes}m"
                        break
                    else:
                        print("❌ Please enter 1, 5, 15, or 30")
                except ValueError:
                    print("❌ Please enter a valid integer")
            
            # Confirm configuration
            print(f"\n📋 CONFIGURATION SUMMARY:")
            print(f"💰 Base Amount: ${base_amount:.2f}")
            print(f"📈 Multiplier: {multiplier}x")
            print(f"🎯 Asset: {asset}")
            print(f"📈 Direction: {direction.upper()}")
            print(f"⏰ Timeframe: {timeframe} ({duration}s)")
            print(f"🔄 Strategy: 2-Cycle Manual Martingale")
            print(f"📊 Maximum Steps: 4 (2 cycles × 2 steps)")
            
            confirm = input("\n✅ Confirm configuration? (y/n): ").lower().strip()
            if confirm != 'y':
                return None
            
            return {
                'base_amount': base_amount,
                'multiplier': multiplier,
                'asset': asset,
                'direction': direction,
                'timeframe': timeframe,
                'duration': duration
            }
            
        except KeyboardInterrupt:
            print("\n❌ Configuration cancelled by user.")
            return None
        except Exception as e:
            print(f"❌ Error in configuration: {e}")
            return None

    async def _execute_manual_martingale_trading(self, config: Dict[str, Any]) -> bool:
        """Execute manual martingale trading with 2-cycle strategy.
        
        Returns:
            bool: True if sequence won, False if sequence lost
        """
        logger.info("Starting manual 2-cycle martingale trading.")
        
        initial_balance = await self.client.get_balance()
        sequence_won = False
        
        # Start the 00-second auto-close monitor for manual trading
        auto_close_task = asyncio.create_task(
            self.close_all_positions_at_00_seconds()
        )
        
        try:
            print(f"\n🎯 Manual 2-Cycle Martingale Started")
            print(f"💰 Base Amount: ${config['base_amount']:.2f}")
            print(f"📈 Multiplier: {config['multiplier']}x")
            print(f"🎯 Asset: {config['asset']}")
            print(f"📈 Direction: {config['direction'].upper()}")
            print(f"🔄 Strategy: 2-Cycle Martingale")
            print(f"📊 Maximum Steps: 4 (2 cycles × 2 steps)")
            print(f"⏰ Timeframe: {config['timeframe'].upper()} ({config['duration']}s per trade)")
            
            # Show current account status
            current_mode = self.client.get_account_mode()
            print(f"💼 Current Account: {current_mode}")
            print("-" * 60)
            
            print(f"💰 Initial Balance: ${initial_balance:.2f}")
            print("-" * 60)
            
            # Execute 2-cycle martingale
            trade_results = await self._execute_2_cycle_martingale(config)
            
            # Check if sequence won
            sequence_won = any(result['result'] == 'win' for result in trade_results)
            
        except KeyboardInterrupt:
            print("\n⏹️  Manual trading stopped by user.")
            sequence_won = False
        except Exception as e:
            logger.error(f"Error in manual martingale trading: {e}")
            print(f"❌ Error in manual trading: {e}")
            sequence_won = False
        finally:
            # Cancel the auto-close monitor
            auto_close_task.cancel()
            
            # End the session timing
            self.session_timing.end_session()
            
            # Show final results
            final_balance = await self.client.get_balance()
            net_result = final_balance - initial_balance if "initial_balance" in locals() else 0
            
            print(f"\n🏁 Martingale Sequence Results:")
            print(f"💰 Initial Balance: ${initial_balance:.2f}")
            print(f"💰 Final Balance: ${final_balance:.2f}")
            
            if net_result >= 0:
                print(f"🎉 Net Sequence Profit: ${net_result:.2f}")
            else:
                print(f"💔 Net Sequence Loss: ${abs(net_result):.2f}")
                
            # Display trade statistics
            if trade_results:
                total_trades = len(trade_results)
                total_wins = len([r for r in trade_results if r['result'] == 'win'])
                total_losses = len([r for r in trade_results if r['result'] == 'loss'])
                win_rate = (total_wins / total_trades) * 100 if total_trades > 0 else 0
                
                print(f"\n📊 Sequence Statistics:")
                print(f"📈 Total Trades: {total_trades}")
                print(f"🎉 Wins: {total_wins}")
                print(f"💔 Losses: {total_losses}")
                print(f"📊 Win Rate: {win_rate:.1f}%")
                
                print(f"\n📋 Trade Details:")
                for i, result in enumerate(trade_results, 1):
                    status_emoji = "🎉" if result['result'] == 'win' else "💔"
                    cycle_info = f"C{result.get('cycle', 1)}S{result.get('step', i)}"
                    timing_info = ""
                    if 'timing' in result and result['timing'] and result['timing'].execution_time:
                        timing_info = f" ({result['timing'].execution_time:.3f}s)"
                    print(f"{status_emoji} {cycle_info}: {result['asset']} {result['direction'].upper()} - {result['result'].upper()} (${result['amount']:.2f}){timing_info}")
            
            # Display comprehensive session timing summary
            self.display_session_timing_summary()
                
            logger.info(f"Manual 2-cycle martingale trading completed. Net result: ${net_result:.2f}")
            
        return sequence_won

    async def _execute_2_cycle_martingale(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute 2-cycle martingale with automatic cycle 2 progression."""
        all_trade_results = []
        base_amount = config['base_amount']
        multiplier = config['multiplier']
        
        # Execute Cycle 1
        print(f"\n🔄 === CYCLE 1 ===")
        cycle_1_results = await self._execute_single_cycle(
            config['asset'], config['direction'], base_amount, multiplier, config, 1
        )
        all_trade_results.extend(cycle_1_results)
        
        # Check if Cycle 1 won
        cycle_1_won = any(result['result'] == 'win' for result in cycle_1_results)
        
        if cycle_1_won:
            print(f"🎉 Cycle 1 WON! Martingale sequence completed successfully.")
            return all_trade_results
        
        # Cycle 1 lost both steps - start Cycle 2
        print(f"💔 Cycle 1 LOST both steps! Starting Cycle 2...")
        
        # Calculate Cycle 2 starting amount (Cycle 1 last step amount × multiplier)
        cycle_1_last_amount = base_amount * multiplier  # Step 2 amount from Cycle 1
        cycle_2_starting_amount = cycle_1_last_amount * multiplier
        
        print(f"📊 Cycle 2 starting amount: ${cycle_2_starting_amount:.2f} (Cycle 1 last step × {multiplier})")
        
        # Get new asset and direction for Cycle 2
        cycle_2_config = await self._get_cycle_2_inputs(config, cycle_2_starting_amount)
        if not cycle_2_config:
            print("❌ Cycle 2 cancelled by user.")
            return all_trade_results
        
        # Execute Cycle 2
        print(f"\n🔄 === CYCLE 2 ===")
        cycle_2_results = await self._execute_single_cycle(
            cycle_2_config['asset'], cycle_2_config['direction'], 
            cycle_2_starting_amount, multiplier, cycle_2_config, 2
        )
        all_trade_results.extend(cycle_2_results)
        
        return all_trade_results

    async def _get_cycle_2_inputs(self, original_config: Dict[str, Any], starting_amount: float) -> Optional[Dict[str, Any]]:
        """Get user inputs for Cycle 2."""
        try:
            print(f"\n" + "=" * 60)
            print("⚙️  CYCLE 2 CONFIGURATION")
            print("=" * 60)
            print(f"💰 Cycle 2 Starting Amount: ${starting_amount:.2f}")
            print(f"📈 Multiplier: {original_config['multiplier']}x (unchanged)")
            print("=" * 60)
            
            # Get new asset for Cycle 2
            print("📊 CYCLE 2 ASSET SELECTION")
            print("=" * 40)
            print("Common assets:")
            print("• EURUSD_otc, GBPUSD_otc, USDJPY_otc")
            print("• EURJPY_otc, GBPJPY_otc, AUDUSD_otc")
            print("• USDCAD_otc, NZDUSD_otc, EURGBP_otc")
            print("=" * 40)
            
            asset = input(f"Enter asset for Cycle 2 (current: {original_config['asset']}): ").strip()
            if not asset:
                asset = original_config['asset']  # Use same asset if empty
                print(f"✅ Using same asset: {asset}")
            
            # Get new direction for Cycle 2
            print("\n📈 CYCLE 2 DIRECTION SELECTION")
            print("=" * 40)
            while True:
                direction = input(f"Enter direction for Cycle 2 (call/put, current: {original_config['direction']}): ").strip().lower()
                if direction == "":
                    direction = original_config['direction']  # Use same direction if empty
                    print(f"✅ Using same direction: {direction.upper()}")
                    break
                elif direction in ['call', 'put']:
                    break
                else:
                    print("❌ Please enter 'call' or 'put', or press Enter to keep current")
            
            # Confirm Cycle 2 configuration
            print(f"\n📋 CYCLE 2 CONFIGURATION SUMMARY:")
            print(f"💰 Starting Amount: ${starting_amount:.2f}")
            print(f"📈 Multiplier: {original_config['multiplier']}x")
            print(f"🎯 Asset: {asset}")
            print(f"📈 Direction: {direction.upper()}")
            print(f"⏰ Timeframe: {original_config['timeframe']} ({original_config['duration']}s)")
            
            confirm = input("\n✅ Confirm Cycle 2 configuration? (y/n): ").lower().strip()
            if confirm != 'y':
                return None
            
            # Create Cycle 2 config
            cycle_2_config = original_config.copy()
            cycle_2_config['asset'] = asset
            cycle_2_config['direction'] = direction
            cycle_2_config['base_amount'] = starting_amount  # Override base amount for Cycle 2
            
            return cycle_2_config
            
        except KeyboardInterrupt:
            print("\n❌ Cycle 2 configuration cancelled by user.")
            return None
        except Exception as e:
            print(f"❌ Error in Cycle 2 configuration: {e}")
            return None

    async def _execute_single_cycle(self, asset: str, direction: str, base_amount: float, 
                                   multiplier: float, config: Dict[str, Any], cycle: int) -> List[Dict[str, Any]]:
        """Execute a single cycle (2 steps) of martingale."""
        cycle_results = []
        
        for step in range(1, 3):  # Steps 1 and 2
            # Calculate amount for this step
            if step == 1:
                amount = base_amount
            else:
                amount = base_amount * multiplier
            
            print(f"\n🔄 Cycle {cycle}, Step {step}")
            print(f"💰 Amount: ${amount:.2f}")
            print(f"🎯 Asset: {asset}")
            print(f"📈 Direction: {direction.upper()}")
            print(f"⏰ Duration: {config['duration']}s")
            
            # Create timing info for this trade
            trade_timing = TradeTimingInfo(
                trade_id=f"manual_c{cycle}s{step}",
                asset=asset,
                direction=direction,
                amount=amount,
                start_time=time.time()
            )
            
            # Execute the trade
            result = await self._execute_manual_single_trade(
                asset, direction, amount, config['duration'], trade_timing, cycle, step
            )
            
            cycle_results.append(result)
            
            # Add timing to session
            self.session_timing.add_trade_timing(trade_timing)
            
            # Check result
            if result['result'] == 'win':
                print(f"🎉 Cycle {cycle}, Step {step} WON! Cycle completed successfully.")
                break  # Exit cycle - won
            elif result['result'] == 'loss':
                print(f"💔 Cycle {cycle}, Step {step} LOST.")
                if step == 2:
                    print(f"💔 Cycle {cycle} completed with all losses.")
                else:
                    print(f"📈 Continuing to Step {step + 1}...")
            else:
                print(f"⚠️ Cycle {cycle}, Step {step} - {result['result']}")
                break  # Exit cycle on error or asset closed
        
        return cycle_results

    async def _execute_manual_single_trade(self, asset: str, direction: str, amount: float, 
                                         duration: int, timing: TradeTimingInfo, cycle: int, step: int) -> Dict[str, Any]:
        """Execute a single manual trade."""
        try:
            # Mark trade setup start
            timing.mark_setup_start()
            
            # Check if asset is available
            asset_name, asset_data = await self.client.get_available_asset(asset, force_open=True)
            
            if not asset_data or len(asset_data) < 3 or not asset_data[2]:
                print(f"❌ Asset {asset} is closed")
                timing.complete_trade("asset_closed", 0)
                return {
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'asset_closed',
                    'profit_loss': 0,
                    'timing': timing
                }
            
            print(f"✅ Asset {asset} is open")
            
            # Execute trade
            timing.mark_trade_placed()
            status, buy_info = await self.client.buy(amount, asset_name, direction, duration, time_mode="TIMER")
            
            if not status:
                print(f"❌ Trade execution failed: {buy_info}")
                timing.complete_trade("trade_failed", 0)
                return {
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'trade_failed',
                    'profit_loss': 0,
                    'timing': timing
                }
            
            trade_id = buy_info.get('id', 'N/A')
            timing.trade_id = str(trade_id)
            
            print(f"✅ Trade executed - ID: {trade_id}")
            print(f"⏳ Waiting {duration}s for result...")
            
            # Wait for trade duration
            await asyncio.sleep(duration + 2)  # Add 2 second buffer
            
            # Check result
            timing.mark_result_checked()
            if await self.client.check_win(trade_id):
                profit = self.client.get_profit()
                print(f"🎉 WIN! Profit: ${profit:.2f}")
                timing.complete_trade("win", profit)
                return {
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'win',
                    'profit_loss': profit,
                    'trade_id': trade_id,
                    'timing': timing
                }
            else:
                loss = amount
                print(f"💔 LOSS: ${loss:.2f}")
                timing.complete_trade("loss", -loss)
                return {
                    'asset': asset,
                    'direction': direction,
                    'amount': amount,
                    'cycle': cycle,
                    'step': step,
                    'result': 'loss',
                    'profit_loss': -loss,
                    'trade_id': trade_id,
                    'timing': timing
                }
                
        except Exception as e:
            print(f"❌ Error executing trade: {e}")
            logger.error(f"Error in manual single trade: {e}")
            timing.complete_trade("error", 0)
            return {
                'asset': asset,
                'direction': direction,
                'amount': amount,
                'cycle': cycle,
                'step': step,
                'result': 'error',
                'profit_loss': 0,
                'error': str(e),
                'timing': timing
            }