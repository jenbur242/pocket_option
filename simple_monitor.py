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
        
        # HARDCODED TARGET CHANNEL - PocketOption Channel
        self.target_invite_link = "https://t.me/pocketoption0o"
        self.target_hash = "pocketoption0o"  # Public channel username
        self.target_channel_id = None  # Will be set when channel is found
        self.target_channel_name = None  # Will be set when channel is found
        
        # Initialize CSV
        self.init_csv()
        
        # Load saved target channel ID if exists
        self.load_target_channel_id()
    
    def load_target_channel_id(self):
        """Load the saved target channel ID from file"""
        try:
            if os.path.exists('.target_channel_id'):
                with open('.target_channel_id', 'r') as f:
                    data = f.read().strip().split('|')
                    if len(data) == 2:
                        self.target_channel_id = int(data[0])
                        self.target_channel_name = data[1]
                        print(f"📋 Loaded saved target channel: {self.target_channel_name} (ID: {self.target_channel_id})")
        except Exception as e:
            print(f"⚠️ Could not load saved channel ID: {e}")
    
    def save_target_channel_id(self, channel_id: int, channel_name: str):
        """Save the target channel ID to file"""
        try:
            with open('.target_channel_id', 'w') as f:
                f.write(f"{channel_id}|{channel_name}")
            self.target_channel_id = channel_id
            self.target_channel_name = channel_name
            print(f"💾 Saved target channel: {channel_name} (ID: {channel_id})")
        except Exception as e:
            print(f"⚠️ Could not save channel ID: {e}")
    
    def init_csv(self):
        """Initialize CSV file with exact format requested - date-based filename"""
        # Delete previous date CSV files to keep only current day's file
        self.cleanup_old_csv_files()
        
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
    
    def cleanup_old_csv_files(self):
        """Delete CSV files from previous dates"""
        try:
            import glob
            
            # Find all CSV files matching the pattern
            csv_pattern = "pocketoption_messages_*.csv"
            existing_csv_files = glob.glob(csv_pattern)
            
            current_date = datetime.now().strftime('%Y%m%d')
            current_csv = f"pocketoption_messages_{current_date}.csv"
            
            deleted_count = 0
            for csv_file in existing_csv_files:
                if csv_file != current_csv:
                    try:
                        os.remove(csv_file)
                        print(f"🗑️  Deleted old CSV: {csv_file}")
                        deleted_count += 1
                    except Exception as e:
                        print(f"⚠️  Could not delete {csv_file}: {e}")
            
            if deleted_count > 0:
                print(f"✅ Cleaned up {deleted_count} old CSV file(s)")
            else:
                print("📊 No old CSV files to clean up")
                
        except Exception as e:
            print(f"⚠️  Error during CSV cleanup: {e}")
    
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
            "💰 Positive execution on **EURUSD-OTC**! Strong reading and flawless setup! 🔥",  # This should NOT be saved
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
        """Save ONLY trading signals to CSV (is_signal = Yes)"""
        try:
            # Parse signal
            signal_data = self.parse_signal(message_text)
            
            # ONLY save to CSV if it's a valid trading signal
            if signal_data['is_signal'] == 'Yes':
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
                print(f"🎯 [{self.message_count}] SIGNAL SAVED: {signal_data['asset']} {signal_data['direction'].upper()} @ {signal_data['signal_time']}")
            else:
                # Just show the message but don't save to CSV
                print(f"💬 Message (not saved): {message_text[:50]}...")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
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
            print("🚫 ONLY this specific channel will be monitored")
            
            target_chat = None
            channel_name = "Unknown Channel"
            
            # Try to join the target channel
            try:
                print("📥 Attempting to access target channel...")
                
                # Check if it's a public channel (starts with @) or private (invite hash)
                if self.target_hash.startswith('@') or not self.target_hash.startswith('+'):
                    # Public channel - try to get entity directly
                    print(f"🔍 Accessing public channel: {self.target_hash}")
                    target_chat = await self.client.get_entity(self.target_hash)
                    channel_name = target_chat.title
                    print(f"✅ Successfully accessed public channel: {channel_name}")
                else:
                    # Private channel - use invite link
                    print(f"🔍 Joining private channel using invite hash: {self.target_hash}")
                    result = await self.client(ImportChatInviteRequest(self.target_hash))
                    if result.chats:
                        target_chat = result.chats[0]
                        channel_name = target_chat.title
                        print(f"✅ Successfully joined private channel: {channel_name}")
                    else:
                        print("❌ No chat returned from invite")
                        return
                
                print(f"📊 Channel ID: {target_chat.id}")
                # Save the channel ID for future use
                self.save_target_channel_id(target_chat.id, channel_name)
                
            except Exception as join_error:
                error_msg = str(join_error).lower()
                
                if "expired" in error_msg:
                    print(f"❌ Invite link has EXPIRED: {join_error}")
                    print("💡 Please get a fresh invite link from the channel admin")
                elif "already a participant" in error_msg:
                    print("✅ Already a member of the target channel")
                    print("🔍 Searching for the channel in your chat list...")
                    
                    # Try to find the channel in existing chats
                    found_target = False
                    async for dialog in self.client.iter_dialogs():
                        if hasattr(dialog.entity, 'title'):
                            # Look for channels that might match our target
                            # You can customize this search logic based on channel name patterns
                            title_lower = dialog.entity.title.lower()
                            if any(keyword in title_lower for keyword in ['signal', 'vip', 'trading', 'pocket', 'option']):
                                print(f"📢 Found potential channel: {dialog.entity.title} (ID: {dialog.entity.id})")
                                
                                # Ask user to confirm or manually select
                                # For now, we'll be strict and not auto-select
                    
                    if not found_target:
                        print("❌ Could not automatically find the target channel")
                        print("🔍 Available channels in your chat list:")
                        count = 0
                        async for dialog in self.client.iter_dialogs(limit=20):
                            if hasattr(dialog.entity, 'title'):
                                print(f"   {count+1}. {dialog.entity.title} (ID: {dialog.entity.id})")
                                count += 1
                        print("\n💡 To fix this:")
                        print("   1. Get a fresh invite link from the channel admin")
                        print("   2. Or manually update the target_hash in the code")
                        return
                elif "not found" in error_msg or "invalid" in error_msg:
                    print(f"❌ Channel not found or invalid: {join_error}")
                    print("💡 Please check the channel link/username is correct")
                else:
                    print(f"❌ Error accessing target channel: {join_error}")
                
                print("🚫 Cannot access target channel - monitor will NOT run")
                print("💡 Make sure you have access to the target channel")
                print(f"   Target: {self.target_invite_link}")
                return
            
            if not target_chat:
                print("❌ No target channel found - stopping monitor")
                return
            
            print(f"✅ MONITORING ONLY: {channel_name}")
            print(f"📊 Channel ID: {target_chat.id}")
            print(f"🎯 This is the ONLY channel being monitored")
            print(f"✅ CSV file: {self.csv_file}")
            
            # Fetch recent messages first (last 10 messages to check for signals)
            print("📥 Fetching recent messages from TARGET CHANNEL ONLY...")
            print("🎯 Only saving TRADING SIGNALS to CSV (is_signal = Yes)")
            try:
                recent_messages = await self.client.get_messages(target_chat, limit=10)
                signals_found = 0
                for message in reversed(recent_messages):  # Process oldest first
                    if message.text:
                        # Parse to check if it's a signal before processing
                        signal_data = self.parse_signal(message.text)
                        if signal_data['is_signal'] == 'Yes':
                            signals_found += 1
                        self.save_message(channel_name, message.id, message.text)
                        await asyncio.sleep(0.1)  # Small delay between saves
                print(f"✅ Processed {len(recent_messages)} recent messages")
                print(f"🎯 Found {signals_found} trading signals and saved to CSV")
            except Exception as fetch_error:
                print(f"⚠️ Could not fetch recent messages: {fetch_error}")
            
            print("👂 Listening for NEW TRADING SIGNALS from TARGET CHANNEL ONLY...")
            print(f"🚫 Ignoring ALL other channels (only monitoring {channel_name})")
            print("🎯 Only TRADING SIGNALS will be saved to CSV")
            print("🔄 Checking for new messages every 2 seconds...")
            print("Press Ctrl+C to stop")
            
            # Store the last message ID to track new messages
            last_message_id = 0
            if recent_messages:
                last_message_id = recent_messages[0].id
            
            # Monitor ONLY this specific channel for NEW trading signals
            @self.client.on(events.NewMessage(chats=target_chat.id))
            async def handle_message(event):
                try:
                    message = event.message
                    if message.text:
                        # Verify this message is from our target channel
                        if event.chat_id == target_chat.id:
                            # Check if it's a trading signal before announcing
                            signal_data = self.parse_signal(message.text)
                            if signal_data['is_signal'] == 'Yes':
                                print(f"🚨 NEW TRADING SIGNAL from {channel_name}!")
                            else:
                                print(f"📨 New message from {channel_name} (not a signal)")
                            self.save_message(channel_name, message.id, message.text)
                        else:
                            print(f"⚠️ Received message from wrong channel (ID: {event.chat_id}) - ignoring")
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
            
            # Additional polling mechanism - check every 2 seconds for new messages
            async def poll_for_messages():
                nonlocal last_message_id
                poll_count = 0
                while True:
                    try:
                        poll_count += 1
                        current_time = datetime.now().strftime('%H:%M:%S')
                        
                        # Show polling activity every 2 seconds
                        print(f"🔄 [{current_time}] Checking Telegram... (Poll #{poll_count})")
                        
                        # Get latest messages since last check
                        new_messages = await self.client.get_messages(target_chat, limit=5)
                        
                        new_message_found = False
                        for message in reversed(new_messages):
                            if message.id > last_message_id and message.text:
                                # This is a new message
                                new_message_found = True
                                signal_data = self.parse_signal(message.text)
                                if signal_data['is_signal'] == 'Yes':
                                    print(f"🚨 [{current_time}] NEW TRADING SIGNAL from {channel_name}!")
                                    print(f"    📊 {signal_data['asset']} {signal_data['direction'].upper()} @ {signal_data['signal_time']}")
                                else:
                                    print(f"📨 [{current_time}] New message from {channel_name} (not a signal)")
                                    print(f"    💬 {message.text[:100]}...")
                                
                                self.save_message(channel_name, message.id, message.text)
                                last_message_id = message.id
                        
                        if not new_message_found:
                            print(f"    ✅ No new messages")
                        
                        await asyncio.sleep(2)  # Wait exactly 2 seconds before next check
                        
                    except Exception as e:
                        print(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] Polling error: {e}")
                        await asyncio.sleep(2)  # Still wait 2 seconds on error
            
            # Start both event listener and polling
            print("🔄 Monitor is running with REAL-TIME polling (every 2 seconds)...")
            print(f"📊 CSV file: {self.csv_file}")
            print("🎯 Non-signal messages are displayed but not saved")
            
            # Run polling in background
            polling_task = asyncio.create_task(poll_for_messages())
            
            try:
                await self.client.run_until_disconnected()
            finally:
                polling_task.cancel()
            
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
    
    print("🚀 TELEGRAM CHANNEL MONITOR - SIGNALS ONLY")
    print("=" * 50)
    print(f"🎯 HARDCODED TARGET: https://t.me/+ZuCrnz2Yv99lNTg5")
    print("📊 CSV Format: timestamp,channel,message_id,message_text,is_signal,asset,direction,signal_time")
    print(f"📅 Date-based filename: pocketoption_messages_{datetime.now().strftime('%Y%m%d')}.csv")
    print("🚫 ONLY fetches from this specific channel")
    print("🎯 ONLY saves TRADING SIGNALS to CSV (is_signal = Yes)")
    print("💬 Other messages are displayed but not saved")
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
