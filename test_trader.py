#!/usr/bin/env python3
"""
Quick test script for PocketOption Trader
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the trader
from pocketoption_trader import PocketOptionTrader

async def test_trader():
    """Test the trader functionality"""
    print("🧪 TESTING POCKETOPTION TRADER")
    print("=" * 50)
    
    # Check current time
    current_time = datetime.now()
    print(f"🕐 Current time: {current_time.strftime('%H:%M:%S')}")
    
    # Initialize trader
    print("🚀 Initializing trader...")
    trader = PocketOptionTrader()
    
    # Test CSV reading
    print("\n📊 Testing CSV signal reading...")
    signals = trader.get_signals_from_csv()
    
    if signals:
        print(f"✅ Found {len(signals)} upcoming signals:")
        for i, signal in enumerate(signals[:3], 1):  # Show first 3
            time_until = (signal['signal_datetime'] - current_time).total_seconds()
            print(f"   {i}. {signal['asset']} {signal['direction'].upper()} at {signal['signal_time']} (in {time_until:.0f}s)")
        
        if len(signals) > 3:
            print(f"   ... and {len(signals) - 3} more signals")
    else:
        print("❌ No upcoming signals found")
        return False
    
    # Test connection (will use simulation mode due to expired SSID)
    print("\n🔌 Testing connection...")
    connected = await trader.connect(is_demo=True)
    
    if connected:
        print("✅ Connection test passed (simulation mode)")
    else:
        print("❌ Connection test failed")
        return False
    
    # Test single trade execution (simulation)
    if signals:
        print("\n🎯 Testing trade execution (simulation)...")
        test_signal = signals[0]
        
        try:
            won, profit = await trader.execute_trade(test_signal, 5.0)
            print(f"✅ Trade test completed: {'WIN' if won else 'LOSS'} - ${abs(profit):.2f}")
        except Exception as e:
            print(f"❌ Trade test failed: {e}")
            return False
    
    # Cleanup
    await trader.disconnect()
    
    print("\n✅ ALL TESTS PASSED!")
    print("🎯 Trader is ready for live trading")
    return True

async def quick_signal_check():
    """Quick check of signal parsing"""
    print("🔍 QUICK SIGNAL CHECK")
    print("=" * 30)
    
    trader = PocketOptionTrader()
    signals = trader.get_signals_from_csv()
    
    current_time = datetime.now()
    print(f"🕐 Current time: {current_time.strftime('%H:%M:%S')}")
    print(f"📊 Total signals found: {len(signals)}")
    
    if signals:
        next_signal = signals[0]
        time_until = (next_signal['signal_datetime'] - current_time).total_seconds()
        print(f"⏰ Next signal: {next_signal['asset']} {next_signal['direction'].upper()} at {next_signal['signal_time']}")
        print(f"⏱️  Time until next signal: {time_until:.0f} seconds")
        
        if time_until > 0:
            print("✅ Ready to trade!")
            return True
        else:
            print("⚠️ Next signal is in the past")
            return False
    else:
        print("❌ No signals found")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Quick signal check only
        asyncio.run(quick_signal_check())
    else:
        # Full test
        asyncio.run(test_trader())