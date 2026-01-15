#!/usr/bin/env python3
"""
Check if assets in CSV are properly formatted
Compares last 10 Telegram messages with CSV entries
"""
import os
import re
import asyncio
import pandas as pd
from datetime import datetime
from telethon import TelegramClient
from dotenv import load_dotenv
from pocketoptionapi_async.constants import ASSETS

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE = os.getenv('TELEGRAM_PHONE')

# Channel to monitor (use invite link)
CHANNEL_ID = 'https://t.me/+ZuCrnz2Yv99lNTg5'
CHANNEL_NAME = 'james martin vip channel m1'

# Cross pairs that need _otc suffix
CROSS_PAIRS = {
    'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'CADCHF', 'CADJPY', 'CHFJPY',
    'CHFNOK', 'EURCHF', 'EURGBP', 'EURHUF', 'EURJPY', 'EURNZD', 'EURRUB',
    'GBPAUD', 'GBPJPY', 'NZDJPY', 'USDRUB', 'NZDCAD'
}

# Exotic pairs that need _otc suffix
EXOTIC_PAIRS = {
    'AEDCNY', 'BHDCNY', 'OMRCNY', 'QARCNY', 'QARUSD', 'QARJPY',
    'NGNUSD', 'USDEGP', 'EGPUSD', 'USDPKR', 'USDBDT', 'CNYQAR',
    'USDCLP', 'CLPUSD', 'USDCOP', 'USDBRL', 'BRLUSD'
}

# Major pairs that work without _otc
MAJOR_PAIRS = {'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD', 'AUDUSD', 'NZDUSD'}

def extract_asset_from_message(text):
    """Extract asset name from Telegram message"""
    if not text:
        return None
    
    # Pattern: • **ASSET** - CALL/PUT
    pattern = r'\*\*([A-Z]{6,})\*\*\s*-\s*(CALL|PUT|call|put)'
    match = re.search(pattern, text)
    
    if match:
        return match.group(1).upper()
    
    return None

def get_correct_asset_format(asset):
    """Determine correct asset format for API"""
    if not asset:
        return None, "No asset"
    
    asset_upper = asset.upper()
    
    # Check if already has _otc
    if asset_upper.endswith('_OTC'):
        base_asset = asset_upper[:-4]
        if base_asset in MAJOR_PAIRS:
            return asset_upper, f"⚠️ Major pair with _otc (should be {base_asset})"
        elif base_asset in CROSS_PAIRS or base_asset in EXOTIC_PAIRS:
            return asset_upper, "✅ Correct format"
        else:
            return asset_upper, "❓ Unknown asset with _otc"
    
    # No _otc suffix
    if asset_upper in MAJOR_PAIRS:
        return asset_upper, "✅ Correct format (major pair)"
    elif asset_upper in CROSS_PAIRS:
        return f"{asset_upper}_otc", f"❌ Missing _otc (should be {asset_upper}_otc)"
    elif asset_upper in EXOTIC_PAIRS:
        return f"{asset_upper}_otc", f"❌ Missing _otc (should be {asset_upper}_otc)"
    else:
        return asset_upper, "❓ Unknown asset"

def check_asset_in_api(asset):
    """Check if asset exists in PocketOption API"""
    if not asset:
        return False, "No asset"
    
    if asset in ASSETS:
        return True, f"✅ In API (ID: {ASSETS[asset]})"
    else:
        return False, "❌ Not in API"

async def check_last_messages():
    """Check last 10 messages from Telegram channel"""
    print("=" * 80)
    print("🔍 CHECKING TELEGRAM MESSAGES vs CSV ASSETS")
    print("=" * 80)
    
    # Initialize Telegram client
    client = TelegramClient('check_assets_session', API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE)
        print(f"✅ Connected to Telegram")
        
        # Get channel using invite link
        channel = await client.get_entity(CHANNEL_ID)
        print(f"✅ Found channel: {channel.title}")
        
        # Get last 50 messages (to find signals)
        messages = []
        async for message in client.iter_messages(channel, limit=50):
            if message.text:
                messages.append({
                    'id': message.id,
                    'date': message.date,
                    'text': message.text
                })
        
        print(f"\n📨 Analyzing last {len(messages)} messages...")
        print("=" * 80)
        
        # Extract assets from messages
        telegram_assets = []
        for msg in messages:
            asset = extract_asset_from_message(msg['text'])
            if asset:
                correct_format, status = get_correct_asset_format(asset)
                in_api, api_status = check_asset_in_api(correct_format)
                
                telegram_assets.append({
                    'message_id': msg['id'],
                    'date': msg['date'],
                    'extracted_asset': asset,
                    'correct_format': correct_format,
                    'format_status': status,
                    'in_api': in_api,
                    'api_status': api_status
                })
                
                print(f"\n📍 Message ID: {msg['id']}")
                print(f"   Date: {msg['date'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   Extracted: {asset}")
                print(f"   Correct Format: {correct_format}")
                print(f"   Format Status: {status}")
                print(f"   API Status: {api_status}")
        
        if not telegram_assets:
            print("\n⚠️ No assets found in last 10 messages")
            return
        
        # Check CSV
        print("\n" + "=" * 80)
        print("📊 CHECKING CSV FILE")
        print("=" * 80)
        
        today = datetime.now().strftime('%Y%m%d')
        csv_file = f"pocketoption_james_martin_vip_channel_m1_{today}.csv"
        
        if not os.path.exists(csv_file):
            print(f"❌ CSV file not found: {csv_file}")
            return
        
        print(f"✅ Found CSV: {csv_file}")
        
        # Read CSV
        df = pd.read_csv(csv_file)
        signals_df = df[df['is_signal'] == 'Yes'].copy()
        
        print(f"📈 Total signals in CSV: {len(signals_df)}")
        
        # Compare with Telegram messages
        print("\n" + "=" * 80)
        print("🔄 COMPARISON: Telegram vs CSV")
        print("=" * 80)
        
        issues_found = []
        
        for tg_asset in telegram_assets:
            msg_id = tg_asset['message_id']
            extracted = tg_asset['extracted_asset']
            correct = tg_asset['correct_format']
            
            # Find in CSV
            csv_match = signals_df[signals_df['message_id'] == msg_id]
            
            if csv_match.empty:
                print(f"\n⚠️ Message {msg_id} ({extracted}) not found in CSV")
                issues_found.append(f"Message {msg_id} missing from CSV")
            else:
                csv_asset = csv_match.iloc[0]['asset']
                print(f"\n✓ Message {msg_id}:")
                print(f"   Telegram: {extracted}")
                print(f"   CSV: {csv_asset}")
                print(f"   Correct: {correct}")
                
                if csv_asset != correct:
                    print(f"   ❌ MISMATCH! CSV should be: {correct}")
                    issues_found.append(f"Message {msg_id}: CSV has '{csv_asset}' but should be '{correct}'")
                else:
                    print(f"   ✅ CORRECT!")
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 SUMMARY")
        print("=" * 80)
        
        if issues_found:
            print(f"\n❌ Found {len(issues_found)} issues:")
            for i, issue in enumerate(issues_found, 1):
                print(f"   {i}. {issue}")
        else:
            print("\n✅ All assets are correctly formatted in CSV!")
        
        # Show asset format guide
        print("\n" + "=" * 80)
        print("📖 ASSET FORMAT GUIDE")
        print("=" * 80)
        print("\n✅ Major Pairs (NO _otc needed):")
        print(f"   {', '.join(sorted(MAJOR_PAIRS))}")
        print("\n⚠️ Cross Pairs (NEED _otc):")
        print(f"   {', '.join(sorted(list(CROSS_PAIRS)[:10]))}...")
        print("\n⚠️ Exotic Pairs (NEED _otc):")
        print(f"   {', '.join(sorted(list(EXOTIC_PAIRS)[:10]))}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.disconnect()
        print("\n✅ Disconnected from Telegram")

async def main():
    """Main function"""
    await check_last_messages()

if __name__ == "__main__":
    asyncio.run(main())
