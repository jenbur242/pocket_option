#!/usr/bin/env python3
"""
Setup $1 CALL trades for PocketOption
Simple script to configure and execute CALL trades with $1 investment
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# Import PocketOption API
from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection
from pocketoptionapi_async.constants import ASSETS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class OneDollarCallTrader:
    """$1 CALL trade setup and execution"""
    
    def __init__(self):
        self.trade_amount = 1.0  # Fixed $1 per trade
        self.client = None
        
        # Recommended assets for CALL trades (high liquidity)
        self.recommended_assets = [
            "EURUSD",      # Euro/US Dollar
            "GBPUSD",      # British Pound/US Dollar  
            "USDJPY",      # US Dollar/Japanese Yen
            "AUDUSD",      # Australian Dollar/US Dollar
            "USDCAD",      # US Dollar/Canadian Dollar
            "EURGBP",      # Euro/British Pound
            "EURJPY",      # Euro/Japanese Yen
            "GBPJPY",      # British Pound/Japanese Yen
        ]
        
        print("💰 $1 CALL Trader Setup")
        print(f"   Fixed Amount: ${self.trade_amount}")
        print(f"   Trade Type: CALL (Buy/Up)")
        print(f"   Recommended Assets: {len(self.recommended_assets)} available")
    
    async def initialize(self):
        """Initialize connection to PocketOption"""
        try:
            email = os.getenv('POCKETOPTION_EMAIL')
            password = os.getenv('POCKETOPTION_PASSWORD')
            
            if not email or not password:
                print("❌ Missing credentials in .env file")
                print("   Add POCKETOPTION_EMAIL and POCKETOPTION_PASSWORD")
                return False
            
            print("🔌 Connecting to PocketOption...")
            
            self.client = AsyncPocketOptionClient()
            await self.client.connect()
            
            login_success = await self.client.login(email, password)
            
            if login_success:
                balance = await self.client.get_balance()
                print(f"✅ Connected successfully")
                print(f"💳 Account Balance: ${balance:.2f}")
                
                if balance < self.trade_amount:
                    print(f"⚠️ Warning: Balance (${balance:.2f}) is less than trade amount (${self.trade_amount})")
                
                return True
            else:
                print("❌ Login failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_available_assets(self) -> List[str]:
        """Get assets available for trading"""
        available = []
        
        print("\n🔍 Checking asset availability:")
        
        for asset in self.recommended_assets:
            if asset in ASSETS:
                available.append(asset)
                print(f"   ✅ {asset} (ID: {ASSETS[asset]})")
            else:
                print(f"   ❌ {asset} (not available)")
        
        return available
    
    async def setup_call_trade(self, asset: str, duration_minutes: int = 1) -> Dict:
        """Setup a CALL trade for specified asset"""
        
        if asset not in ASSETS:
            return {
                "success": False,
                "error": f"Asset {asset} not available",
                "asset": asset
            }
        
        trade_config = {
            "asset": asset,
            "asset_id": ASSETS[asset],
            "amount": self.trade_amount,
            "direction": "CALL",
            "duration_minutes": duration_minutes,
            "duration_seconds": duration_minutes * 60,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print(f"\n📋 Trade Configuration:")
        print(f"   Asset: {asset} (ID: {ASSETS[asset]})")
        print(f"   Amount: ${self.trade_amount}")
        print(f"   Direction: CALL (Buy/Up)")
        print(f"   Duration: {duration_minutes} minute(s)")
        print(f"   Expected Return: ~80-85% if successful")
        
        return {
            "success": True,
            "config": trade_config
        }
    
    async def execute_call_trade(self, asset: str, duration_minutes: int = 1) -> Dict:
        """Execute a CALL trade"""
        
        if not self.client:
            return {"success": False, "error": "Not connected"}
        
        try:
            print(f"\n🚀 Executing CALL trade...")
            print(f"   Asset: {asset}")
            print(f"   Amount: ${self.trade_amount}")
            print(f"   Direction: CALL")
            
            # Place the order
            result = await self.client.place_order(
                asset=asset,
                amount=self.trade_amount,
                direction=OrderDirection.CALL,
                duration=duration_minutes * 60
            )
            
            if result and hasattr(result, 'order_id'):
                print(f"✅ Trade executed successfully!")
                print(f"   Order ID: {result.order_id}")
                print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                
                return {
                    "success": True,
                    "order_id": result.order_id,
                    "asset": asset,
                    "amount": self.trade_amount,
                    "direction": "CALL",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"❌ Trade execution failed")
                return {"success": False, "error": "Order placement failed"}
                
        except Exception as e:
            print(f"❌ Execution error: {e}")
            return {"success": False, "error": str(e)}
    
    async def batch_call_trades(self, assets: List[str], duration_minutes: int = 1) -> List[Dict]:
        """Execute multiple CALL trades"""
        
        results = []
        total_investment = len(assets) * self.trade_amount
        
        print(f"\n🎯 Batch CALL Trades Setup:")
        print(f"   Assets: {', '.join(assets)}")
        print(f"   Trades: {len(assets)}")
        print(f"   Amount per trade: ${self.trade_amount}")
        print(f"   Total investment: ${total_investment}")
        print(f"   Duration: {duration_minutes} minute(s)")
        
        # Confirm batch execution
        confirm = input(f"\nExecute {len(assets)} CALL trades for ${total_investment}? (y/N): ")
        
        if confirm.lower() != 'y':
            print("❌ Batch execution cancelled")
            return []
        
        print(f"\n🚀 Executing batch trades...")
        
        for i, asset in enumerate(assets, 1):
            print(f"\n[{i}/{len(assets)}] Processing {asset}...")
            
            result = await self.execute_call_trade(asset, duration_minutes)
            results.append(result)
            
            # Small delay between trades
            if i < len(assets):
                await asyncio.sleep(1)
        
        # Summary
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]
        
        print(f"\n📊 Batch Results:")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        print(f"   💰 Total invested: ${len(successful) * self.trade_amount}")
        
        return results
    
    async def disconnect(self):
        """Disconnect from API"""
        if self.client:
            await self.client.disconnect()
            print("🔌 Disconnected from PocketOption")

async def main():
    """Main trading function"""
    
    trader = OneDollarCallTrader()
    
    try:
        # Initialize connection
        if not await trader.initialize():
            return
        
        # Get available assets
        available_assets = trader.get_available_assets()
        
        if not available_assets:
            print("❌ No assets available for trading")
            return
        
        print(f"\n📈 Available for CALL trades: {len(available_assets)} assets")
        
        while True:
            print("\n" + "="*50)
            print("💰 $1 CALL TRADER OPTIONS")
            print("="*50)
            print("1. Single CALL trade")
            print("2. Multiple CALL trades")
            print("3. Show available assets")
            print("4. Quick trade on EURUSD")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                # Single trade
                print(f"\nAvailable assets:")
                for i, asset in enumerate(available_assets, 1):
                    print(f"   {i}. {asset}")
                
                try:
                    selection = int(input(f"Select asset (1-{len(available_assets)}): ")) - 1
                    if 0 <= selection < len(available_assets):
                        asset = available_assets[selection]
                        duration = int(input("Duration in minutes (1-5, default 1): ") or "1")
                        
                        # Setup and execute
                        setup = await trader.setup_call_trade(asset, duration)
                        if setup["success"]:
                            confirm = input("Execute this trade? (y/N): ")
                            if confirm.lower() == 'y':
                                await trader.execute_call_trade(asset, duration)
                    else:
                        print("❌ Invalid selection")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == "2":
                # Multiple trades
                print("Select assets for batch CALL trades:")
                print("Enter numbers separated by commas (e.g., 1,2,3) or 'all'")
                
                for i, asset in enumerate(available_assets, 1):
                    print(f"   {i}. {asset}")
                
                selection = input("Your selection: ").strip()
                
                if selection.lower() == "all":
                    selected_assets = available_assets
                else:
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(",")]
                        selected_assets = [available_assets[i] for i in indices if 0 <= i < len(available_assets)]
                    except:
                        print("❌ Invalid selection")
                        continue
                
                if selected_assets:
                    duration = int(input("Duration in minutes (1-5, default 1): ") or "1")
                    await trader.batch_call_trades(selected_assets, duration)
                else:
                    print("❌ No valid assets selected")
            
            elif choice == "3":
                # Show assets
                trader.get_available_assets()
            
            elif choice == "4":
                # Quick EURUSD trade
                if "EURUSD" in available_assets:
                    print("🚀 Quick EURUSD CALL trade...")
                    await trader.execute_call_trade("EURUSD", 1)
                else:
                    print("❌ EURUSD not available")
            
            elif choice == "5":
                # Exit
                break
            
            else:
                print("❌ Invalid option")
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    
    finally:
        await trader.disconnect()

if __name__ == "__main__":
    print("🚀 Starting $1 CALL Trader...")
    asyncio.run(main())