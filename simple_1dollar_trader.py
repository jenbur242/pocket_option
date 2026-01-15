#!/usr/bin/env python3
"""
Simple $1 CALL Trader for PocketOption
Takes $1 as input and executes CALL trades on specified assets
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dotenv import load_dotenv

# Import PocketOption API
from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection, OrderStatus
from pocketoptionapi_async.constants import ASSETS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDollarTrader:
    """Simple $1 trader for CALL operations"""
    
    def __init__(self, trade_amount: float = 1.0):
        self.trade_amount = trade_amount
        self.client = None
        self.is_connected = False
        
        # Default assets for trading (major pairs)
        self.default_assets = [
            "EURUSD",
            "GBPUSD", 
            "USDJPY",
            "USDCAD",
            "AUDUSD"
        ]
        
        print(f"💰 Simple Dollar Trader Initialized")
        print(f"   Trade Amount: ${self.trade_amount}")
        print(f"   Default Assets: {', '.join(self.default_assets)}")
    
    async def connect(self):
        """Connect to PocketOption API"""
        try:
            # Get credentials from environment
            email = os.getenv('POCKETOPTION_EMAIL')
            password = os.getenv('POCKETOPTION_PASSWORD')
            
            if not email or not password:
                raise ValueError("Missing POCKETOPTION_EMAIL or POCKETOPTION_PASSWORD in .env file")
            
            print("🔌 Connecting to PocketOption...")
            
            # Initialize client
            self.client = AsyncPocketOptionClient()
            
            # Connect and login
            await self.client.connect()
            login_result = await self.client.login(email, password)
            
            if login_result:
                self.is_connected = True
                print("✅ Successfully connected to PocketOption")
                
                # Get account info
                balance = await self.client.get_balance()
                print(f"💳 Account Balance: ${balance:.2f}")
                
                return True
            else:
                print("❌ Failed to login to PocketOption")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from PocketOption API"""
        if self.client and self.is_connected:
            await self.client.disconnect()
            self.is_connected = False
            print("🔌 Disconnected from PocketOption")
    
    def validate_asset(self, asset: str) -> bool:
        """Validate if asset exists in our constants"""
        return asset in ASSETS
    
    async def place_call_trade(self, asset: str, duration_minutes: int = 1) -> Dict[str, Any]:
        """Place a CALL trade on specified asset"""
        if not self.is_connected:
            return {"success": False, "error": "Not connected to API"}
        
        if not self.validate_asset(asset):
            return {"success": False, "error": f"Asset {asset} not found in supported assets"}
        
        try:
            print(f"📈 Placing CALL trade: {asset} - ${self.trade_amount} - {duration_minutes}m")
            
            # Place the trade
            result = await self.client.place_order(
                asset=asset,
                amount=self.trade_amount,
                direction=OrderDirection.CALL,
                duration=duration_minutes * 60  # Convert to seconds
            )
            
            if result and hasattr(result, 'order_id'):
                print(f"✅ Trade placed successfully!")
                print(f"   Order ID: {result.order_id}")
                print(f"   Asset: {asset}")
                print(f"   Amount: ${self.trade_amount}")
                print(f"   Direction: CALL")
                print(f"   Duration: {duration_minutes} minutes")
                
                return {
                    "success": True,
                    "order_id": result.order_id,
                    "asset": asset,
                    "amount": self.trade_amount,
                    "direction": "CALL",
                    "duration": duration_minutes
                }
            else:
                print(f"❌ Failed to place trade on {asset}")
                return {"success": False, "error": "Trade placement failed"}
                
        except Exception as e:
            print(f"❌ Error placing trade on {asset}: {e}")
            return {"success": False, "error": str(e)}
    
    async def place_multiple_calls(self, assets: List[str], duration_minutes: int = 1) -> List[Dict[str, Any]]:
        """Place CALL trades on multiple assets"""
        results = []
        
        print(f"\n🚀 Starting multiple CALL trades...")
        print(f"   Assets: {', '.join(assets)}")
        print(f"   Amount per trade: ${self.trade_amount}")
        print(f"   Total investment: ${self.trade_amount * len(assets)}")
        
        for asset in assets:
            result = await self.place_call_trade(asset, duration_minutes)
            results.append(result)
            
            # Small delay between trades
            await asyncio.sleep(0.5)
        
        # Summary
        successful_trades = [r for r in results if r.get("success")]
        failed_trades = [r for r in results if not r.get("success")]
        
        print(f"\n📊 Trade Summary:")
        print(f"   ✅ Successful: {len(successful_trades)}")
        print(f"   ❌ Failed: {len(failed_trades)}")
        print(f"   💰 Total invested: ${len(successful_trades) * self.trade_amount}")
        
        return results
    
    async def get_available_assets(self) -> List[str]:
        """Get list of available assets for trading"""
        available = []
        
        print("🔍 Checking available assets...")
        
        for asset in self.default_assets:
            if self.validate_asset(asset):
                available.append(asset)
                print(f"   ✅ {asset}")
            else:
                print(f"   ❌ {asset} (not available)")
        
        return available

async def interactive_trader():
    """Interactive trading session"""
    trader = SimpleDollarTrader(trade_amount=1.0)
    
    try:
        # Connect to API
        if not await trader.connect():
            return
        
        while True:
            print("\n" + "="*60)
            print("💰 SIMPLE $1 CALL TRADER")
            print("="*60)
            print("1. Place single CALL trade")
            print("2. Place multiple CALL trades")
            print("3. Show available assets")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                # Single trade
                print("\nAvailable assets:")
                available = await trader.get_available_assets()
                for i, asset in enumerate(available, 1):
                    print(f"   {i}. {asset}")
                
                try:
                    asset_choice = int(input(f"\nSelect asset (1-{len(available)}): ")) - 1
                    if 0 <= asset_choice < len(available):
                        asset = available[asset_choice]
                        duration = int(input("Enter duration in minutes (default 1): ") or "1")
                        
                        result = await trader.place_call_trade(asset, duration)
                        
                        if result["success"]:
                            print(f"\n🎉 Trade placed successfully!")
                        else:
                            print(f"\n❌ Trade failed: {result.get('error')}")
                    else:
                        print("❌ Invalid asset selection")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == "2":
                # Multiple trades
                available = await trader.get_available_assets()
                print(f"\nAvailable assets: {', '.join(available)}")
                
                asset_input = input("Enter assets (comma-separated) or 'all' for all available: ").strip()
                
                if asset_input.lower() == "all":
                    selected_assets = available
                else:
                    selected_assets = [a.strip().upper() for a in asset_input.split(",")]
                    # Validate assets
                    selected_assets = [a for a in selected_assets if a in available]
                
                if selected_assets:
                    duration = int(input("Enter duration in minutes (default 1): ") or "1")
                    
                    # Confirm trade
                    total_cost = len(selected_assets) * trader.trade_amount
                    print(f"\n📋 Trade Confirmation:")
                    print(f"   Assets: {', '.join(selected_assets)}")
                    print(f"   Amount per trade: ${trader.trade_amount}")
                    print(f"   Total cost: ${total_cost}")
                    
                    confirm = input("Confirm trades? (y/N): ").strip().lower()
                    
                    if confirm == 'y':
                        results = await trader.place_multiple_calls(selected_assets, duration)
                    else:
                        print("❌ Trades cancelled")
                else:
                    print("❌ No valid assets selected")
            
            elif choice == "3":
                # Show available assets
                await trader.get_available_assets()
            
            elif choice == "4":
                # Exit
                print("👋 Exiting trader...")
                break
            
            else:
                print("❌ Invalid option")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    
    finally:
        await trader.disconnect()

async def quick_call_trade(asset: str = "EURUSD", duration: int = 1):
    """Quick function to place a single $1 CALL trade"""
    trader = SimpleDollarTrader(trade_amount=1.0)
    
    try:
        if await trader.connect():
            result = await trader.place_call_trade(asset, duration)
            return result
        else:
            return {"success": False, "error": "Connection failed"}
    
    finally:
        await trader.disconnect()

def main():
    """Main function"""
    print("🚀 Starting Simple $1 CALL Trader...")
    
    # Check environment variables
    if not os.getenv('POCKETOPTION_EMAIL') or not os.getenv('POCKETOPTION_PASSWORD'):
        print("❌ Missing credentials in .env file")
        print("   Please add POCKETOPTION_EMAIL and POCKETOPTION_PASSWORD")
        return
    
    # Run interactive trader
    asyncio.run(interactive_trader())

if __name__ == "__main__":
    main()