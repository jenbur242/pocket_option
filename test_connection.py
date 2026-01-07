#!/usr/bin/env python3
"""
Simple connection test for PocketOption API
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_connection():
    """Test PocketOption connection"""
    print("🧪 TESTING POCKETOPTION CONNECTION")
    print("=" * 50)
    
    # Check SSID
    ssid = os.getenv('SSID')
    if not ssid:
        print("❌ No SSID found in .env file")
        return False
    
    print(f"✅ SSID found: {ssid[:50]}...")
    print(f"🎯 Account type: {'REAL' if 'isDemo\":0' in ssid else 'DEMO'}")
    
    try:
        from pocketoptionapi_async import AsyncPocketOptionClient
        print("✅ PocketOption API imported successfully")
        
        # Create client
        client = AsyncPocketOptionClient(
            ssid=ssid,
            is_demo=True,  # Test on demo account
            persistent_connection=True
        )
        
        print("🔌 Attempting to connect...")
        await client.connect()
        
        if client.is_connected:
            print("✅ Connection successful!")
            
            # Test balance
            try:
                balance = await client.get_balance()
                print(f"💰 Balance: ${balance}")
            except Exception as e:
                print(f"⚠️  Balance check failed: {e}")
            
            # Disconnect
            await client.disconnect()
            print("🔌 Disconnected successfully")
            return True
        else:
            print("❌ Connection failed")
            return False
            
    except ImportError:
        print("❌ PocketOption API not available")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())