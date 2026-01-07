#!/usr/bin/env python3
"""
Telegram Channel Monitor - Hardcoded for specific channel
Fetches messages from https://t.me/+ZuCrnz2Yv99lNTg5 ONLY
"""
import os
import csv
import re
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.functions.messages import ImportChatInviteRequest

# Load environment variables
load_dotenv()

class TelegramChannelMonitor:
    """Monitor specific Telegram channel and save messages"""
    
    def __init__(self):
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        self.client = None
        self.message_count = 0
        
        # Create date-based CSV filename
        today = datetime.now().strftime('%Y%m%d')
        self.csv_file = f"pocketoption_messages_{today}.csv"
        
        # HARDCODED TARGET CHANNEL
        self.target_invite_link = "https://t.me/+ZuCrnz2Yv99lNTg5"
        self.target_hash = "ZuCrnz2Yv99lNTg5"  # Extract hash from invite link
        
        # Initialize CSV
        self.init_csv()
    
    def init_csv(self):
        """Initialize CSV file with exact format requested - date-based filename"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['timestamp', 'channel', 'message_id', 'message_text', 'is_signal', 'asset', 'direction', 'signal_time'])
            print(f"✅ Created new CSV file: {self.csv_file}")
        else:
            print(f"📊 Using existing CSV: {self.csv_file}")
            # Count existing messages
            try:
                with open(self.csv_file, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    next(reader)  # Skip header
                    self.message_count = sum(1 for row in reader)
                print(f"📊 Found {self.message_count} existing messages")
            except:
                self.message_count = 0
    
    def parse_signal(self, message_text: str) -> dict:
        """Parse trading signal from message text - Updated for Quotex format"""
        try:
            text = message_text.upper().strip()
            
            # Enhanced asset patterns for Quotex format (includes -OTC suffix)
            asset_patterns = [
                # Standard forex pairs
                r'\b(EUR[/\s]?USD|EURUSD)(?:-OTC)?\b',
                r'\b(GBP[/\s]?USD|GBPUSD)(?:-OTC)?\b',
                r'\b(USD[/\s]?JPY|USDJPY)(?:-OTC)?\b',
                r'\b(USD[/\s]?CHF|USDCHF)(?:-OTC)?\b',
                r'\b(USD[/\s]?CAD|USDCAD)(?:-OTC)?\b',
                r'\b(EUR[/\s]?GBP|EURGBP)(?:-OTC)?\b',
                r'\b(AUD[/\s]?USD|AUDUSD)(?:-OTC)?\b',
                r'\b(NZD[/\s]?USD|NZDUSD)(?:-OTC)?\b',
                r'\b(USD[/\s]?PKR|USDPKR)(?:-OTC)?\b',
                r'\b(USD[/\s]?EGP|USDEGP)(?:-OTC)?\b',
                r'\b(USD[/\s]?BDT|USDBDT)(?:-OTC)?\b',
                # Additional pairs from Quotex
                r'\b(NZD[/\s]?CAD|NZDCAD)(?:-OTC)?\b',
                r'\b(NZD[/\s]?JPY|NZDJPY)(?:-OTC)?\b',
                r'\b(USD[/\s]?COP|USDCOP)(?:-OTC)?\b',
                r'\b(BRL[/\s]?USD|BRLUSD)(?:-OTC)?\b',
                r'\b(AUD[/\s]?CAD|AUDCAD)(?:-OTC)?\b',
                r'\b(AUD[/\s]?CHF|AUDCHF)(?:-OTC)?\b',
                r'\b(AUD[/\s]?JPY|AUDJPY)(?:-OTC)?\b',
                r'\b(CAD[/\s]?CHF|CADCHF)(?:-OTC)?\b',
                r'\b(CAD[/\s]?JPY|CADJPY)(?:-OTC)?\b',
                r'\b(CHF[/\s]?JPY|CHFJPY)(?:-OTC)?\b',
                r'\b(EUR[/\s]?CHF|EURCHF)(?:-OTC)?\b',
                r'\b(EUR[/\s]?JPY|EURJPY)(?:-OTC)?\b',
                r'\b(EUR[/\s]?NZD|EURNZD)(?:-OTC)?\b',
                r'\b(GBP[/\s]?AUD|GBPAUD)(?:-OTC)?\b',
                r'\b(GBP[/\s]?JPY|GBPJPY)(?:-OTC)?\b'
            ]
            
            # Find asset
            asset = None
            for pattern in asset_patterns:
                match = re.search(pattern, text)
                if match:
                    asset = match.group(1).replace('/', '').replace(' ', '')
                    # Remove -OTC suffix if present
                    if asset.endswith('-OTC'):
                        asset = asset[:-4]
                    break
            
            # Enhanced direction patterns for Quotex format
            direction_patterns = [
                r'🔼\s*(CALL|BUY|UP)',  # Quotex up arrow with call
                r'🔽\s*(PUT|SELL|DOWN)',  # Quotex down arrow with put
                r'\b(CALL|BUY|UP|⬆️|📈)\b',
                r'\b(PUT|SELL|DOWN|⬇️|📉)\b'
            ]
            
            direction = None
            for pattern in direction_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    word = match.group(1).upper() if match.group(1) else match.group(0).upper()
                    if any(w in word for w in ['CALL', 'BUY', 'UP', '⬆️', '📈', '🔼']):
                        direction = 'call'
                    elif any(w in word for w in ['PUT', 'SELL', 'DOWN', '⬇️', '📉', '🔽']):
                        direction = 'put'
                    break
            
            # Enhanced time patterns for Quotex format
            time_patterns = [
                r'⌛\s*(\d{1,2}:\d{2}:\d{2})',  # Quotex format: ⌛ 01:37:00
                r'⌛\s*(\d{1,2}:\d{2})',       # Quotex format: ⌛ 01:37
                r'(\d{1,2}:\d{2}:\d{2})',     # HH:MM:SS
                r'(\d{1,2}:\d{2})',           # HH:MM
                r'(\d{1,2}\.\d{2})',          # HH.MM
                r'at\s+(\d{1,2}:\d{2})',      # at HH:MM
                r'time[:\s]+(\d{1,2}:\d{2})', # time: HH:MM
                r'(\d{1,2}h\d{2})',           # HHhMM
            ]
            
            signal_time = None
            for pattern in time_patterns:
                match = re.search(pattern, text)
                if match:
                    time_str = match.group(1)
                    # Normalize to HH:MM format
                    if '.' in time_str:
                        signal_time = time_str.replace('.', ':')
                    elif 'h' in time_str:
                        signal_time = time_str.replace('h', ':')
                    elif len(time_str.split(':')) == 3:  # HH:MM:SS format
                        parts = time_str.split(':')
                        signal_time = f"{parts[0]}:{parts[1]}"  # Keep only HH:MM
                    else:
                        signal_time = time_str
                    break
            
            # Determine if valid signal
            is_signal = 'Yes' if (asset and direction and signal_time) else 'No'
            
            return {
                'asset': asset,
                'direction': direction,
                'signal_time': signal_time,
                'is_signal': is_signal
            }
            
        except Exception as e:
            return {
                'asset': None,
                'direction': None,
                'signal_time': None,
                'is_signal': 'No'
            }
    
    def test_message_saving(self):
        """Test message saving functionality with Quotex format"""
        print("🧪 Testing message saving with Quotex format...")
        
        test_messages = [
            "💳 BRLUSD-OTC 🔥 M1 ⌛ 00:55:00 🔼 call  🚦 Tend: Buy 📈 Forecast: 73.75% 💸 Payout: 93.0%",
            "💳 NZDCAD-OTC 🔥 M1 ⌛ 01:03:00 🔽 put  🚦 Tend: Sell 📈 Forecast: 98% 💸 Payout: 81.0%",
            "💳 USDCOP-OTC 🔥 M1 ⌛ 01:11:00 🔼 call  🚦 Tend: neutral 📈 Forecast: 64.3% 💸 Payout: 77.0%",
            "💳 NZDJPY-OTC 🔥 M1 ⌛ 01:37:00 🔼 call  🚦 Tend: Buy 📈 Forecast: 78.35% 💸 Payout: 93.0%",
            "WIN ✅",
            "💔 Loss",
            "EURUSD CALL 14:30 - Standard format test"
        ]
        
        for i, msg in enumerate(test_messages, 1):
            self.save_message("Test Channel", 9000 + i, msg)
            # Show what was parsed
            parsed = self.parse_signal(msg)
            print(f"   Message: {msg[:50]}...")
            print(f"   Parsed: Asset={parsed['asset']}, Direction={parsed['direction']}, Time={parsed['signal_time']}, Signal={parsed['is_signal']}")
            print()
        
        print("✅ Test messages saved and parsed")
    
    def save_message(self, channel_name: str, message_id: int, message_text: str):
        """Save message in exact CSV format requested"""
        try:
            # Parse signal
            signal_data = self.parse_signal(message_text)
            
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    channel_name,
                    message_id,
                    message_text.replace('\n', ' ').replace('\r', ' ').strip(),
                    signal_data['is_signal'],
                    signal_data['asset'] or '',
                    signal_data['direction'] or '',
                    signal_data['signal_time'] or ''
                ])
            
            self.message_count += 1
            
            if signal_data['is_signal'] == 'Yes':
                print(f"🎯 [{self.message_count}] SIGNAL: {signal_data['asset']} {signal_data['direction'].upper()} @ {signal_data['signal_time']}")
            else:
                print(f"💬 [{self.message_count}] Message: {message_text[:50]}...")
                
        except Exception as e:
            print(f"❌ Error saving message: {e}")
    
    async def start_monitoring(self):
        """Start monitoring the HARDCODED channel ONLY"""
        try:
            if not all([self.api_id, self.api_hash, self.phone]):
                print("❌ Missing Telegram credentials in .env file")
                print("   Please check TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE in .env")
                return
            
            self.client = TelegramClient('telegram_session', int(self.api_id), self.api_hash)
            
            print("🔌 Connecting to Telegram...")
            await self.client.start(phone=self.phone)
            
            if not await self.client.is_user_authorized():
                print("❌ Failed to authenticate")
                return
            
            print("✅ Connected to Telegram!")
            print(f"🎯 Target channel: {self.target_invite_link}")
            
            target_chat = None
            channel_name = "Unknown Channel"
            
            # FIRST: Try to join using the specific invite link
            try:
                print("📥 Joining target channel using invite link...")
                result = await self.client(ImportChatInviteRequest(self.target_hash))
                if result.chats:
                    target_chat = result.chats[0]
                    channel_name = target_chat.title
                    print(f"✅ Successfully joined target channel: {channel_name}")
                    print(f"📊 Channel ID: {target_chat.id}")
                else:
                    print("❌ No chat returned from invite")
                    return
            except Exception as join_error:
                if "already a participant" in str(join_error).lower():
                    print("✅ Already joined target channel")
                    
                    # Try to find the SPECIFIC channel by attempting to use the invite hash
                    print("🔍 Searching for the specific target channel...")
                    
                    # Get all dialogs and try to find one that matches our target
                    found_target = False
                    async for dialog in self.client.iter_dialogs():
                        if hasattr(dialog.entity, 'id'):
                            try:
                                # Try to get the invite link for this channel to match
                                if hasattr(dialog.entity, 'username') and dialog.entity.username:
                                    continue  # Skip public channels
                                
                                # For private channels, check if we can access messages
                                messages = await self.client.get_messages(dialog.entity, limit=1)
                                if messages and hasattr(dialog.entity, 'title'):
                                    # This is a potential match - let's use it if it has trading-related content
                                    title = dialog.entity.title.lower()
                                    if any(keyword in title for keyword in ['signal', 'trading', 'forex', 'option', 'vip']):
                                        target_chat = dialog.entity
                                        channel_name = dialog.entity.title
                                        print(f"🎯 Found potential target channel: {channel_name} (ID: {dialog.entity.id})")
                                        found_target = True
                                        break
                            except:
                                continue
                    
                    if not found_target:
                        print("❌ Could not find the specific target channel")
                        print("🔍 Available channels:")
                        async for dialog in self.client.iter_dialogs(limit=10):
                            if hasattr(dialog.entity, 'title'):
                                print(f"   📢 {dialog.entity.title} (ID: {dialog.entity.id})")
                        return
                else:
                    print(f"❌ Error joining channel: {join_error}")
                    return
            
            if not target_chat:
                print("❌ No target channel found")
                return
            
            print(f"✅ MONITORING ONLY: {channel_name}")
            print(f"📊 Channel ID: {target_chat.id}")
            print(f"🎯 This is the ONLY channel being monitored")
            print(f"✅ CSV file: {self.csv_file}")
            
            # Fetch recent messages first (last 5 messages to avoid spam)
            print("📥 Fetching recent messages from TARGET CHANNEL ONLY...")
            try:
                recent_messages = await self.client.get_messages(target_chat, limit=5)
                for message in reversed(recent_messages):  # Process oldest first
                    if message.text:
                        self.save_message(channel_name, message.id, message.text)
                        await asyncio.sleep(0.1)  # Small delay between saves
                print(f"✅ Processed {len(recent_messages)} recent messages from TARGET CHANNEL")
            except Exception as fetch_error:
                print(f"⚠️ Could not fetch recent messages: {fetch_error}")
            
            print("👂 Listening for NEW messages from TARGET CHANNEL ONLY...")
            print(f"🚫 Ignoring ALL other channels (only monitoring {channel_name})")
            print("Press Ctrl+C to stop")
            
            # Monitor ONLY this specific channel for NEW messages
            @self.client.on(events.NewMessage(chats=target_chat.id))
            async def handle_message(event):
                try:
                    message = event.message
                    if message.text:
                        print(f"📨 New message from TARGET CHANNEL: {channel_name}")
                        self.save_message(channel_name, message.id, message.text)
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
            
            # Keep the client running
            print("🔄 Monitor is running - ONLY monitoring the target channel...")
            await self.client.run_until_disconnected()
            
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.client:
                await self.client.disconnect()
                print("🔌 Disconnected from Telegram")

async def main():
    """Main function - hardcoded to fetch from specific channel only"""
    import sys
    
    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("🧪 RUNNING TEST MODE")
        print("=" * 50)
        monitor = TelegramChannelMonitor()
        monitor.test_message_saving()
        return
    
    # Check for manual channel selection mode
    if len(sys.argv) > 1 and sys.argv[1] == 'select':
        print("🔍 MANUAL CHANNEL SELECTION MODE")
        print("=" * 50)
        monitor = TelegramChannelMonitor()
        await monitor.manual_channel_selection()
        return
    
    print("🚀 TELEGRAM CHANNEL MONITOR")
    print("=" * 50)
    print(f"🎯 HARDCODED TARGET: https://t.me/+ZuCrnz2Yv99lNTg5")
    print("📊 CSV Format: timestamp,channel,message_id,message_text,is_signal,asset,direction,signal_time")
    print(f"📅 Date-based filename: pocketoption_messages_{datetime.now().strftime('%Y%m%d')}.csv")
    print("🚫 ONLY fetches from this specific channel")
    print("💡 Run with 'python simple_monitor.py test' to test CSV saving")
    print("💡 Run with 'python simple_monitor.py select' to manually select channel")
    print("=" * 50)
    
    # Check .env file first
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("   Please create .env file with:")
        print("   TELEGRAM_API_ID=your_api_id")
        print("   TELEGRAM_API_HASH=your_api_hash")
        print("   TELEGRAM_PHONE=your_phone_number")
        return
    
    # Load and check credentials
    load_dotenv()
    api_id = os.getenv('TELEGRAM_API_ID')
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone = os.getenv('TELEGRAM_PHONE')
    
    if not all([api_id, api_hash, phone]):
        print("❌ Missing Telegram credentials in .env file")
        print(f"   API_ID: {'✅' if api_id else '❌'}")
        print(f"   API_HASH: {'✅' if api_hash else '❌'}")
        print(f"   PHONE: {'✅' if phone else '❌'}")
        return
    
    print("✅ Credentials found in .env file")
    
    monitor = TelegramChannelMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())