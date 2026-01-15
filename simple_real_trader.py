#!/usr/bin/env python3
"""
Simple Real Trader using working SSID method from app.py
Executes actual $1 CALL trades on PocketOption
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv

# Import PocketOption API
from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection
from pocketoptionapi_async.constants import ASSETS

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleRealTrader:
    """Simple real trader using proven SSID method"""
    
    def __init__(self, trade_amount: float = 1.0):
        self.trade_amount = trade_amount
        self.ssid = os.getenv('SSID')
        self.client = None
        self.is_connected = False
        
        # Working assets from your existing setup
        self.working_assets = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD',
            'AUDCAD', 'AUDCHF', 'AUDJPY', 'EURCHF', 'EURGBP', 'EURJPY', 'GBPJPY'
        ]
        
        print(f"💰 Simple Real Trader")
        print(f"   Trade Amount: ${self.trade_amount}")
        print(f"   SSID Available: {'✅' if self.ssid else '❌'}")
        print(f"   Working Assets: {len(self.working_assets)}")
    
    async def connect(self, is_demo: bool = True) -> bool:
        """Connect using the same method as app.py"""
        try:
            if not self.ssid:
                print("❌ SSID not found in .env file")
                return False
            
            print(f"🔌 Connecting to PocketOption ({'DEMO' if is_demo else 'REAL'})...")
            print(f"🔑 Using SSID: {self.ssid[:50]}...")
            
            # Use the same connection method as your working app.py
            self.client = AsyncPocketOptionClient(
                ssid=self.ssid,
                is_demo=is_demo,
                region="EUROPA"
            )
            
            # Connect
            connection_result = await self.client.connect()
            
            if connection_result:
                self.is_connected = True
                print("✅ Successfully connected to PocketOption")
                
                # Try to get balance
                try:
                    balance = await self.client.get_balance()
                    print(f"💳 Account Balance: ${balance:.2f}")
                    
                    if balance < self.trade_amount:
                        print(f"⚠️ Warning: Balance (${balance:.2f}) < Trade Amount (${self.trade_amount})")
                    
                    return True
                    
                except Exception as e:
                    print(f"⚠️ Connected but couldn't get balance: {e}")
                    return True  # Still consider it connected
                    
            else:
                print("❌ Failed to connect")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from API"""
        if self.client and self.is_connected:
            try:
                await self.client.disconnect()
                self.is_connected = False
                print("🔌 Disconnected from PocketOption")
            except Exception as e:
                print(f"⚠️ Disconnect error: {e}")
    
    def get_asset_format(self, asset: str) -> str:
        """Get correct asset format for API"""
        # Major pairs use direct format
        major_pairs = {'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD'}
        
        if asset in major_pairs:
            return asset
        else:
            # Cross pairs need _otc suffix
            return f"{asset}_otc"
    
    async def place_real_call_trade(self, asset: str, duration_minutes: int = 1) -> Dict[str, Any]:
        """Place a real CALL trade"""
        
        if not self.is_connected:
            return {"success": False, "error": "Not connected"}
        
        if asset not in self.working_assets:
            return {"success": False, "error": f"Asset {asset} not in working assets"}
        
        # Get correct asset format
        api_asset = self.get_asset_format(asset)
        
        if api_asset not in ASSETS:
            return {"success": False, "error": f"Asset {api_asset} not found in API"}
        
        try:
            print(f"\n🚀 PLACING REAL CALL TRADE")
            print(f"   Asset: {asset} -> {api_asset}")
            print(f"   Amount: ${self.trade_amount}")
            print(f"   Direction: CALL")
            print(f"   Duration: {duration_minutes} minute(s)")
            print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
            
            # Place the order using the same method as app.py
            result = await self.client.place_order(
                asset=api_asset,
                amount=self.trade_amount,
                direction=OrderDirection.CALL,
                duration=duration_minutes * 60
            )
            
            if result and hasattr(result, 'order_id'):
                print(f"✅ TRADE PLACED SUCCESSFULLY!")
                print(f"   Order ID: {result.order_id}")
                print(f"   Asset: {asset} ({api_asset})")
                print(f"   Amount: ${self.trade_amount}")
                print(f"   Expected Return: ~${self.trade_amount * 0.8:.2f} if win")
                
                return {
                    "success": True,
                    "order_id": result.order_id,
                    "asset": asset,
                    "api_asset": api_asset,
                    "amount": self.trade_amount,
                    "direction": "CALL",
                    "duration": duration_minutes,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"❌ TRADE FAILED - No order ID returned")
                return {"success": False, "error": "No order ID returned"}
                
        except Exception as e:
            print(f"❌ TRADE ERROR: {e}")
            return {"success": False, "error": str(e)}
    
    def show_working_assets(self):
        """Show available working assets"""
        print(f"\n📈 Working Assets ({len(self.working_assets)}):")
        
        for i, asset in enumerate(self.working_assets, 1):
            api_asset = self.get_asset_format(asset)
            asset_id = ASSETS.get(api_asset, "Unknown")
            print(f"   {i:2d}. {asset:<8} -> {api_asset:<12} (ID: {asset_id})")

async def demo_test():
    """Test connection in demo mode"""
    print("🧪 Testing connection in DEMO mode...")
    
    trader = SimpleRealTrader(trade_amount=1.0)
    
    try:
        # Test demo connection
        if await trader.connect(is_demo=True):
            print("✅ Demo connection successful")
            
            # Show available assets
            trader.show_working_assets()
            
            # Test a demo trade
            print("\n🧪 Testing demo CALL trade on EURUSD...")
            result = await trader.place_real_call_trade("EURUSD", 1)
            
            if result["success"]:
                print("✅ Demo trade test successful!")
            else:
                print(f"❌ Demo trade test failed: {result['error']}")
        else:
            print("❌ Demo connection failed")
    
    finally:
        await trader.disconnect()

async def real_trading_session():
    """Interactive real trading session"""
    print("💰 REAL TRADING SESSION")
    print("="*50)
    
    # Warning for real money
    print("⚠️ WARNING: This will use REAL MONEY!")
    confirm = input("Type 'YES' to continue with real money trading: ")
    
    if confirm != 'YES':
        print("❌ Real trading cancelled")
        return
    
    trader = SimpleRealTrader(trade_amount=1.0)
    
    try:
        # Connect in real mode
        if not await trader.connect(is_demo=False):
            print("❌ Failed to connect for real trading")
            return
        
        while True:
            print("\n" + "="*50)
            print("💰 REAL TRADING MENU")
            print("="*50)
            print("1. Place single CALL trade")
            print("2. Show working assets")
            print("3. Quick EURUSD trade")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                # Single trade
                trader.show_working_assets()
                
                try:
                    asset_num = int(input(f"\nSelect asset (1-{len(trader.working_assets)}): ")) - 1
                    if 0 <= asset_num < len(trader.working_assets):
                        asset = trader.working_assets[asset_num]
                        duration = int(input("Duration in minutes (1-5, default 1): ") or "1")
                        
                        # Final confirmation
                        print(f"\n📋 Trade Confirmation:")
                        print(f"   Asset: {asset}")
                        print(f"   Amount: ${trader.trade_amount} REAL MONEY")
                        print(f"   Direction: CALL")
                        print(f"   Duration: {duration} minute(s)")
                        
                        final_confirm = input("Execute this REAL trade? Type 'YES': ")
                        
                        if final_confirm == 'YES':
                            result = await trader.place_real_call_trade(asset, duration)
                            
                            if result["success"]:
                                print(f"\n🎉 Real trade executed successfully!")
                                print(f"   Order ID: {result['order_id']}")
                            else:
                                print(f"\n❌ Real trade failed: {result['error']}")
                        else:
                            print("❌ Trade cancelled")
                    else:
                        print("❌ Invalid asset selection")
                except ValueError:
                    print("❌ Invalid input")
            
            elif choice == "2":
                # Show assets
                trader.show_working_assets()
            
            elif choice == "3":
                # Quick EURUSD trade
                print(f"\n🚀 Quick EURUSD CALL trade for ${trader.trade_amount}")
                final_confirm = input("Execute REAL EURUSD trade? Type 'YES': ")
                
                if final_confirm == 'YES':
                    result = await trader.place_real_call_trade("EURUSD", 1)
                    
                    if result["success"]:
                        print(f"🎉 Quick trade successful! Order ID: {result['order_id']}")
                    else:
                        print(f"❌ Quick trade failed: {result['error']}")
                else:
                    print("❌ Quick trade cancelled")
            
            elif choice == "4":
                # Exit
                break
            
            else:
                print("❌ Invalid option")
    
    finally:
        await trader.disconnect()

def main():
    """Main function"""
    print("🚀 Simple Real Trader for PocketOption")
    print("="*50)
    
    if not os.getenv('SSID'):
        print("❌ SSID not found in .env file")
        return
    
    print("Select mode:")
    print("1. Demo test (safe)")
    print("2. Real trading (uses real money)")
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == "1":
        asyncio.run(demo_test())
    elif choice == "2":
        asyncio.run(real_trading_session())
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()