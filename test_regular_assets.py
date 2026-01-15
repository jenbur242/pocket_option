#!/usr/bin/env python3
"""
Test all 21 regular format assets (non-OTC)
Quick verification that all major pairs work
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from pocketoptionapi_async import AsyncPocketOptionClient
from pocketoptionapi_async.models import OrderDirection

load_dotenv()

# All 21 regular format assets
REGULAR_ASSETS = {
    "AUDCAD": 58,
    "AUDCHF": 59,
    "AUDJPY": 60,
    "AUDUSD": 61,
    "CADCHF": 62,
    "CADJPY": 63,
    "CHFJPY": 64,
    "EURAUD": 65,
    "EURCAD": 66,
    "EURCHF": 67,
    "EURGBP": 68,
    "EURJPY": 69,
    "EURUSD": 70,
    "GBPAUD": 71,
    "GBPCAD": 72,
    "GBPCHF": 73,
    "GBPJPY": 74,
    "GBPUSD": 75,
    "USDCAD": 76,
    "USDCHF": 77,
    "USDJPY": 78,
}

async def test_regular_assets():
    """Test all 21 regular format assets"""
    
    ssid = os.getenv('SSID')
    if not ssid:
        print("❌ SSID not found")
        return
    
    print("🧪 TESTING 21 REGULAR FORMAT ASSETS")
    print("="*60)
    print(f"   Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Mode: DEMO (safe testing)")
    print(f"   Trade Amount: $1.00")
    print(f"   Direction: CALL")
    print(f"   Duration: 1 minute")
    
    client = None
    results = []
    
    try:
        # Connect
        print(f"\n🔌 Connecting to PocketOption...")
        
        client = AsyncPocketOptionClient(
            ssid=ssid,
            is_demo=True,
            persistent_connection=False,
            auto_reconnect=False,
            enable_logging=False
        )
        
        await asyncio.wait_for(client.connect(), timeout=15.0)
        balance = await asyncio.wait_for(client.get_balance(), timeout=10.0)
        
        print(f"✅ Connected! Demo Balance: ${balance.balance:.2f}")
        
        # Test each asset
        print(f"\n🚀 Testing {len(REGULAR_ASSETS)} assets...")
        print("="*60)
        
        for i, (asset, asset_id) in enumerate(REGULAR_ASSETS.items(), 1):
            print(f"\n[{i}/21] Testing {asset} (ID: {asset_id})...")
            
            try:
                result = await asyncio.wait_for(
                    client.place_order(
                        asset=asset,
                        amount=1.0,
                        direction=OrderDirection.CALL,
                        duration=60
                    ),
                    timeout=8.0
                )
                
                if result and hasattr(result, 'order_id'):
                    print(f"   ✅ SUCCESS - Order ID: {result.order_id}")
                    results.append({
                        "asset": asset,
                        "asset_id": asset_id,
                        "status": "SUCCESS",
                        "order_id": result.order_id
                    })
                else:
                    print(f"   ❌ FAILED - No order ID")
                    results.append({
                        "asset": asset,
                        "asset_id": asset_id,
                        "status": "NO_ORDER_ID",
                        "order_id": None
                    })
                    
            except asyncio.TimeoutError:
                print(f"   ⏱️ TIMEOUT")
                results.append({
                    "asset": asset,
                    "asset_id": asset_id,
                    "status": "TIMEOUT",
                    "order_id": None
                })
            except Exception as e:
                print(f"   ❌ ERROR - {str(e)}")
                results.append({
                    "asset": asset,
                    "asset_id": asset_id,
                    "status": f"ERROR: {str(e)}",
                    "order_id": None
                })
            
            # Small delay between trades
            if i < len(REGULAR_ASSETS):
                await asyncio.sleep(0.5)
            
            # Progress update every 5 assets
            if i % 5 == 0:
                successful = len([r for r in results if r["status"] == "SUCCESS"])
                print(f"\n   📊 Progress: {i}/21 ({(successful/i)*100:.1f}% success)")
    
    finally:
        if client:
            await client.disconnect()
            print(f"\n🔌 Disconnected")
    
    # Final Report
    print(f"\n" + "="*60)
    print("📊 FINAL RESULTS")
    print("="*60)
    
    successful = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] != "SUCCESS"]
    
    print(f"\n✅ SUCCESSFUL: {len(successful)}/21 ({(len(successful)/21)*100:.1f}%)")
    for result in successful:
        print(f"   • {result['asset']:<8} (ID: {result['asset_id']}) - {result['order_id']}")
    
    if failed:
        print(f"\n❌ FAILED: {len(failed)}/21 ({(len(failed)/21)*100:.1f}%)")
        for result in failed:
            print(f"   • {result['asset']:<8} (ID: {result['asset_id']}) - {result['status']}")
    
    # Summary
    print(f"\n" + "="*60)
    print("🎯 SUMMARY")
    print("="*60)
    print(f"   Total Assets Tested: 21")
    print(f"   ✅ Working: {len(successful)}")
    print(f"   ❌ Not Working: {len(failed)}")
    print(f"   Success Rate: {(len(successful)/21)*100:.1f}%")
    
    if len(successful) == 21:
        print(f"\n🎉 PERFECT! All 21 regular format assets are working!")
    elif len(successful) >= 18:
        print(f"\n✅ EXCELLENT! {len(successful)}/21 assets working!")
    else:
        print(f"\n⚠️ Some assets need attention")
    
    # Save results
    print(f"\n💾 Saving results...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"regular_assets_test_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write(f"Regular Format Assets Test Results\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"="*60 + "\n\n")
        
        f.write(f"SUCCESSFUL ASSETS ({len(successful)}/21):\n")
        for result in successful:
            f.write(f"  {result['asset']:<8} ID: {result['asset_id']}\n")
        
        if failed:
            f.write(f"\nFAILED ASSETS ({len(failed)}/21):\n")
            for result in failed:
                f.write(f"  {result['asset']:<8} ID: {result['asset_id']} - {result['status']}\n")
        
        f.write(f"\nSuccess Rate: {(len(successful)/21)*100:.1f}%\n")
    
    print(f"✅ Results saved to: {filename}")
    
    return results

async def main():
    """Main function"""
    await test_regular_assets()

if __name__ == "__main__":
    asyncio.run(main())