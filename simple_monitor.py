#!/usr/bin/env python3
"""
Simple Monitor - Fetch messages from Telegram channels and save to CSV
Updated with improved LC Trader pattern recognition
"""
import asyncio
import logging
import os
import re
import csv
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon import TelegramClient

# Load environment variables
load_dotenv()

# Disable telethon logging
logging.basicConfig(level=logging.CRITICAL)

class SimpleMonitor:
    def __init__(self):
        # Telegram config
        self.api_id = os.getenv('TELEGRAM_API_ID')
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')
        
        # Initialize clients
        self.telegram_client = None
        
        # Channels to monitor
        self.channels = [
            {
                'id': 'https://t.me/+ZuCrnz2Yv99lNTg5',
                'name': 'james martin vip channel m1',
                'entity': None,
                'last_msg_id': None
            },
            # SECOND CHANNEL COMMENTED OUT
            # {
            #     'id': 'https://t.me/luctrader09',
            #     'name': 'lc trader',
            #     'entity': None,
            #     'last_msg_id': None
            # }
        ]
        
        # CSV file setup - separate file for each channel
        today = datetime.now().strftime('%Y%m%d')
        self.csv_files = {}
        
        # Create CSV file for each channel
        for channel in self.channels:
            # Create safe filename from channel name
            safe_name = re.sub(r'[^\w\s-]', '', channel['name']).strip()
            safe_name = re.sub(r'[-\s]+', '_', safe_name).lower()
            csv_filename = f"pocketoption_{safe_name}_{today}.csv"
            self.csv_files[channel['name']] = csv_filename
        
        # Ensure all CSV files have headers
        self.ensure_csv_headers()
        
        self.current_channel = 0
        self.running = False
        
        # Session statistics
        self.session_start = datetime.now()
        self.signals_detected = 0
        self.messages_processed = 0
        self.last_status_time = None
    
    def ensure_csv_headers(self):
        """Ensure CSV files exist with proper headers for each channel"""
        headers = [
            'timestamp', 'channel', 'message_id', 'message_text', 
            'is_signal', 'asset', 'direction', 'signal_time'
        ]
        
        for channel_name, csv_file in self.csv_files.items():
            # Create directory only if the file path contains a directory
            csv_dir = os.path.dirname(csv_file)
            if csv_dir:  # Only create directory if there's actually a directory path
                os.makedirs(csv_dir, exist_ok=True)
            
            # Check if file exists and has headers
            if not os.path.exists(csv_file):
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                print(f"📄 Created CSV file for {channel_name}: {csv_file}")
            else:
                print(f"📄 Using existing CSV file for {channel_name}: {csv_file}")
    
    async def fetch_last_message_pattern(self, channel):
        """Fetch the last 10 messages from channel to learn pattern"""
        if not channel['entity']:
            return None
        
        try:
            # Get the last 10 messages to analyze patterns
            messages = await self.telegram_client.get_messages(channel['entity'], limit=10)
            
            if not messages:
                print(f"   📭 No messages found in {channel['name']}")
                return None
            
            print(f"\n🔍 ANALYZING LAST 10 MESSAGES for {channel['name']}:")
            print("-" * 60)
            
            patterns_found = []
            
            for i, msg in enumerate(messages):
                if msg.text:
                    print(f"📨 Message {i+1} (ID: {msg.id}):")
                    print(f"   📝 Text: {msg.text[:200]}...")
                    
                    # Analyze for signal patterns
                    signal_data = self.extract_signal_data(msg.text, channel['name'])
                    if signal_data:
                        print(f"   🎯 SIGNAL DETECTED:")
                        print(f"      💰 Asset: {signal_data['asset']}")
                        print(f"      📊 Direction: {signal_data['direction']}")
                        print(f"      ⏰ Time: {signal_data['signal_time'] or 'Not specified'}")
                        patterns_found.append(signal_data)
                    else:
                        # Check for other patterns
                        text_lower = msg.text.lower()
                        if any(word in text_lower for word in ['win', 'result', '✅']):
                            print(f"   📊 RESULT MESSAGE detected")
                        elif any(word in text_lower for word in ['register', 'bonus', 'join']):
                            print(f"   📢 PROMOTIONAL MESSAGE detected")
                        else:
                            print(f"   📝 REGULAR MESSAGE")
                    
                    print()
            
            if patterns_found:
                print(f"✅ Found {len(patterns_found)} signal patterns in last 10 messages from {channel['name']}")
            else:
                print(f"ℹ️ No signal patterns found in last 10 messages from {channel['name']}")
            
            print("-" * 60)
            return patterns_found
            
        except Exception as e:
            print(f"❌ Error fetching patterns from {channel['name']}: {e}")
            return None
    
    async def initialize(self):
        """Initialize clients with session reuse and authentication"""
        try:
            print("🔌 Initializing Telegram connection...")
            
            # Create Telegram client (reuse existing session if available)
            self.telegram_client = TelegramClient('monitor_session', self.api_id, self.api_hash)
            
            # Check if session exists
            session_exists = os.path.exists('monitor_session.session')
            
            if session_exists:
                print("📱 Using existing session...")
                try:
                    await self.telegram_client.start(phone=self.phone)
                    
                    # Test if session is still valid
                    me = await self.telegram_client.get_me()
                    print(f"✅ Session valid - Logged in as: {me.first_name} ({me.phone})")
                    
                except Exception as session_error:
                    print(f"⚠️ Existing session invalid: {session_error}")
                    print("🔄 Creating new session...")
                    
                    # Clean invalid session files
                    session_files = ['monitor_session.session', 'monitor_session.session-journal', 'monitor_session.session-wal']
                    for session_file in session_files:
                        if os.path.exists(session_file):
                            try:
                                os.remove(session_file)
                                print(f"🧹 Cleaned: {session_file}")
                            except Exception as e:
                                print(f"⚠️ Could not remove {session_file}: {e}")
                    
                    # Recreate client and authenticate
                    self.telegram_client = TelegramClient('monitor_session', self.api_id, self.api_hash)
                    await self.authenticate_new_session()
                    
                    # Test new connection
                    me = await self.telegram_client.get_me()
                    print(f"✅ New session created - Logged in as: {me.first_name} ({me.phone})")
            else:
                print("📱 No existing session found - Creating new session...")
                await self.authenticate_new_session()
                
                # Test connection
                me = await self.telegram_client.get_me()
                print(f"✅ New session created - Logged in as: {me.first_name} ({me.phone})")
            
            # Get entities for all channels and analyze patterns
            print("📡 Connecting to channels and analyzing patterns...")
            for channel in self.channels:
                try:
                    # Handle invite link
                    if 'joinchat' in channel['id'] or '+' in channel['id']:
                        # Extract invite hash from link
                        if '+' in channel['id']:
                            invite_hash = channel['id'].split('+')[-1]
                        else:
                            invite_hash = channel['id'].split('/')[-1]
                        
                        # Join channel using invite link
                        try:
                            result = await self.telegram_client.join_chat(invite_hash)
                            entity = result.chats[0]
                        except Exception as join_error:
                            print(f"⚠️ Could not join channel: {join_error}")
                            # Try to get entity directly
                            entity = await self.telegram_client.get_entity(channel['id'])
                    else:
                        entity = await self.telegram_client.get_entity(channel['id'])
                    
                    channel['entity'] = entity
                    
                    # Get the latest message ID to start from
                    messages = await self.telegram_client.get_messages(entity, limit=1)
                    if messages:
                        channel['last_msg_id'] = messages[0].id
                    
                    print(f"✅ {channel['name']}: Connected")
                    
                    # Analyze message patterns from this channel (last 10 messages)
                    await self.fetch_last_message_pattern(channel)
                    
                except Exception as e:
                    print(f"❌ {channel['name']}: Failed to connect - {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    async def authenticate_new_session(self):
        """Handle new session authentication with OTP and password"""
        try:
            print(f"📱 Sending OTP to {self.phone}...")
            
            # Start authentication process (without password_callback)
            await self.telegram_client.start(
                phone=self.phone,
                code_callback=self.get_otp_code
            )
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            raise e
    
    def get_otp_code(self):
        """Get OTP code from user input"""
        print("\n📨 OTP code has been sent to your phone")
        print("💡 Check your Telegram app for the verification code")
        
        while True:
            try:
                code = input("🔢 Enter the OTP code: ").strip()
                if code and len(code) >= 5:
                    return code
                else:
                    print("❌ Invalid code. Please enter the 5-digit code from Telegram")
            except KeyboardInterrupt:
                print("\n🛑 Authentication cancelled")
                raise
            except Exception as e:
                print(f"❌ Error reading code: {e}")
    
    async def handle_2fa_if_needed(self):
        """Handle 2FA password if required"""
        try:
            # Check if 2FA is enabled
            if await self.telegram_client.is_user_authorized():
                return True
            
            print("\n🔐 Two-factor authentication required")
            print("💡 Enter your 2FA password (cloud password)")
            
            while True:
                try:
                    import getpass
                    password = getpass.getpass("🔑 Enter your 2FA password: ").strip()
                    if password:
                        await self.telegram_client.sign_in(password=password)
                        return True
                    else:
                        print("❌ Password cannot be empty")
                except KeyboardInterrupt:
                    print("\n🛑 Authentication cancelled")
                    raise
                except Exception as e:
                    print(f"❌ 2FA failed: {e}")
                    return False
        except Exception as e:
            print(f"❌ 2FA error: {e}")
            return False
    
    def extract_signal_data(self, message_text, channel_name):
        """Extract signal data from message based on channel type"""
        if not message_text:
            return None
        
        # LC Trader channel pattern
        if 'lc trader' in channel_name.lower():
            return self.extract_lc_trader_signal(message_text)
        
        # James Martin VIP channel pattern (original)
        return self.extract_james_martin_signal(message_text)
    
    def extract_lc_trader_signal(self, message_text):
        """Extract signal data from LC Trader message format"""
        # Check for LC Trader signal pattern: "OPPORTUNITY FOUND"
        if "OPPORTUNITY FOUND" not in message_text:
            return None
        
        # Pattern: ASSET_otc—TIME: DIRECTION
        # Example: CHFJPY_otc—05:00: PUT 🔴
        signal_pattern = r'([A-Z]{6})_otc—(\d{2}:\d{2}):\s*(PUT|CALL)'
        
        match = re.search(signal_pattern, message_text, re.IGNORECASE)
        if not match:
            return None
        
        asset = match.group(1).upper() + "_otc"  # CHFJPY_otc
        signal_time = match.group(2)  # 05:00
        direction = match.group(3).lower()  # put or call
        
        return {
            'asset': asset,
            'direction': direction,
            'signal_time': signal_time
        }
    
    def extract_james_martin_signal(self, message_text):
        """Extract signal data from James Martin VIP channel format"""
        # Skip obvious non-signal messages
        skip_words = ['win', 'loss', '💔', '✅', 'register', 'code', 'bonus', 'join', 'channel', 'withdraw', 'verify', 'account']
        if any(skip_word in message_text.lower() for skip_word in skip_words):
            # But allow if it has VIP SIGNAL
            if 'VIP SIGNAL' not in message_text:
                return None
        
        # Must have VIP SIGNAL or signal indicators
        if not any(indicator in message_text for indicator in ['VIP SIGNAL', '💳', '🔥', '⌛', 'CALL', 'PUT']):
            return None
        
        # Extract Asset - preserve full format including OTC
        asset = None
        
        # First try to match full OTC format patterns
        otc_patterns = [
            r'\*\*([A-Z]{6})-OTC[p]?\*\*',   # **GBPUSD-OTC** or **NZDUSD-OTCp**
            r'💳\s*([A-Z]{6})-OTC[p]?',      # 💳 AUDCAD-OTC
            r'([A-Z]{6})-OTC[p]?\s*-\s*(CALL|PUT)', # GBPUSD-OTC - PUT
            r'([A-Z]{6})-OTC[p]?',           # AUDCAD-OTC
            r'📊\s*([A-Z]{6})-OTC[p]?',      # 📊 AUDCAD-OTC
        ]
        
        # Check for OTC format first
        for pattern in otc_patterns:
            asset_match = re.search(pattern, message_text, re.IGNORECASE)
            if asset_match:
                base_asset = asset_match.group(1).upper()
                if len(base_asset) == 6:  # Ensure it's a valid currency pair
                    asset = f"{base_asset}_otc"  # Convert GBPUSD to GBPUSD_otc
                    break
        
        # If no OTC format found, try regular patterns
        if not asset:
            regular_patterns = [
                r'\*\*([A-Z]{6})\*\*',           # **GBPUSD**
                r'💳\s*([A-Z]{6})\s',            # 💳 AUDCAD 
                r'📊\s*([A-Z]{6})',              # 📊 AUDCAD
            ]
            
            for pattern in regular_patterns:
                asset_match = re.search(pattern, message_text, re.IGNORECASE)
                if asset_match:
                    asset = asset_match.group(1).upper()
                    # Ensure it's 6 characters (currency pair)
                    if len(asset) == 6:
                        break
        
        if not asset:
            return None
        
        # Extract time
        signal_time = None
        time_patterns = [
            r'PUT\s*🟥\s*-\s*(\d{1,2}:\d{2})',  # PUT 🟥 - 00:37
            r'CALL\s*🟩\s*-\s*(\d{1,2}:\d{2})', # CALL 🟩 - 00:37
            r'-\s*(\d{1,2}:\d{2})\s*•',         # - 21:32 •
            r'⌛\s*(\d{1,2}:\d{2}:\d{2})',      # ⌛ 12:25:00
            r'⌛\s*(\d{1,2}:\d{2})',           # ⌛ 12:25
            r'⏰\s*(\d{1,2}:\d{2})',           # ⏰ 12:25
            r'-\s*(\d{1,2}:\d{2})$',           # - 21:32 at end
            r'(\d{1,2}:\d{2})\s*•',            # 21:32 •
        ]
        
        for pattern in time_patterns:
            time_match = re.search(pattern, message_text)
            if time_match:
                signal_time = time_match.group(1)
                break
        
        # Extract direction
        direction = None
        if '🔽' in message_text or 'PUT' in message_text.upper() or 'DOWN' in message_text.upper() or '🟥' in message_text:
            direction = 'put'
        elif '🔼' in message_text or 'CALL' in message_text.upper() or 'UP' in message_text.upper() or '🟩' in message_text:
            direction = 'call'
        
        if not direction:
            return None
        
        return {
            'asset': asset,
            'direction': direction,
            'signal_time': signal_time
        }
    
    def save_to_csv(self, channel, message, signal_data=None):
        """Save message to channel-specific CSV file"""
        try:
            # Get the CSV file for this channel
            csv_file = self.csv_files.get(channel['name'])
            if not csv_file:
                print(f"❌ No CSV file found for channel: {channel['name']}")
                return False
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Prepare row data
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                channel_name = channel['name']
                message_id = message.id
                message_text = message.text.replace('\n', ' ').replace('\r', ' ') if message.text else ''
                
                if signal_data:
                    is_signal = 'Yes'
                    asset = signal_data['asset']
                    direction = signal_data['direction']
                    signal_time = signal_data['signal_time'] or ''
                    
                    # Debug logging for signal data
                    print(f"   💾 Saving signal to {csv_file}: {asset} {direction} at {signal_time}")
                else:
                    is_signal = 'No'
                    asset = ''
                    direction = ''
                    signal_time = ''
                
                row = [timestamp, channel_name, message_id, message_text, 
                       is_signal, asset, direction, signal_time]
                
                writer.writerow(row)
                return True
                
        except Exception as e:
            print(f"         ❌ CSV save error: {e}")
            return False
    
    async def check_channel(self, channel):
        """Check one channel for new messages"""
        if not channel['entity']:
            return
        
        try:
            # Get latest messages (check more messages for better detection)
            messages = await self.telegram_client.get_messages(channel['entity'], limit=10)
            
            new_messages_found = False
            
            for msg in messages:
                # Skip if we've already seen this message
                if channel['last_msg_id'] and msg.id <= channel['last_msg_id']:
                    continue
                
                new_messages_found = True
                self.messages_processed += 1
                
                # Update last seen message ID
                if not channel['last_msg_id'] or msg.id > channel['last_msg_id']:
                    channel['last_msg_id'] = msg.id
                
                if msg.text:
                    # Show message in real-time format
                    time_str = datetime.now().strftime('%H:%M:%S')
                    message_preview = msg.text.replace('\n', ' ')[:150]
                    print(f"\n🔔 [{time_str}] NEW MESSAGE from {channel['name']}:")
                    print(f"   📝 {message_preview}")
                    
                    # Check if it's a signal with detailed analysis (pass channel name)
                    signal_data = self.extract_signal_data(msg.text, channel['name'])
                    
                    # Save to CSV
                    saved = self.save_to_csv(channel, msg, signal_data)
                    
                    if signal_data:
                        self.signals_detected += 1
                        # Show detailed signal info
                        save_status = "✅ SAVED TO CSV" if saved else "❌ SAVE FAILED"
                        print(f"   🎯 TRADING SIGNAL DETECTED:")
                        print(f"      💰 Asset: {signal_data['asset']}")
                        print(f"      📊 Direction: {signal_data['direction'].upper()}")
                        print(f"      ⏰ Time: {signal_data['signal_time'] or 'Not specified'}")
                        print(f"      💾 Status: {save_status}")
                        print(f"      📊 Session Signals: {self.signals_detected}")
                        print(f"   🚨 READY FOR TRADING!")
                    else:
                        # Check if it's a result message
                        if any(word in msg.text.lower() for word in ['win', 'result', '✅', 'confirmed', 'victory', 'gain']):
                            save_status = "📊 RESULT SAVED" if saved else "❌ SAVE FAILED"
                            print(f"   📊 RESULT MESSAGE: {save_status}")
                        else:
                            save_status = "📝 MESSAGE SAVED" if saved else "❌ SAVE FAILED"
                            print(f"   📝 Status: {save_status}")
                    
                    # Show which CSV file was used
                    csv_file = self.csv_files.get(channel['name'], 'Unknown')
                    print(f"   📄 CSV: {csv_file}")
                    print("-" * 60)
                else:
                    # Media message
                    saved = self.save_to_csv(channel, msg, None)
                    time_str = datetime.now().strftime('%H:%M:%S')
                    print(f"\n🔔 [{time_str}] NEW MEDIA MESSAGE from {channel['name']}")
                    save_status = "📷 MEDIA SAVED" if saved else "❌ SAVE FAILED"
                    print(f"   📷 Status: {save_status}")
                    csv_file = self.csv_files.get(channel['name'], 'Unknown')
                    print(f"   📄 CSV: {csv_file}")
                    print("-" * 60)
            
            # Show monitoring status every 30 seconds if no new messages
            if not new_messages_found:
                current_time = datetime.now()
                if self.last_status_time is None:
                    self.last_status_time = current_time
                
                if (current_time - self.last_status_time).seconds >= 30:
                    time_str = current_time.strftime('%H:%M:%S')
                    print(f"⏰ [{time_str}] Monitoring {channel['name']} - No new messages")
                    self.last_status_time = current_time
        
        except Exception as e:
            error_msg = str(e).lower()
            time_str = datetime.now().strftime('%H:%M:%S')
            
            # Handle specific database errors
            if 'readonly database' in error_msg or 'database is locked' in error_msg:
                print(f"🔄 [{time_str}] Database issue detected - recreating session...")
                # Try to recreate the session
                try:
                    await self.telegram_client.disconnect()
                    await asyncio.sleep(2)
                    
                    # Clean session files
                    session_files = ['monitor_session.session', 'monitor_session.session-journal', 'monitor_session.session-wal']
                    for session_file in session_files:
                        if os.path.exists(session_file):
                            try:
                                os.remove(session_file)
                            except:
                                pass
                    
                    # Recreate client
                    self.telegram_client = TelegramClient('monitor_session', self.api_id, self.api_hash)
                    await self.authenticate_new_session()
                    
                    # Reconnect to channels
                    await self.reconnect_channels()
                    print(f"✅ [{time_str}] Session recreated successfully")
                    
                except Exception as reconnect_error:
                    print(f"❌ [{time_str}] Failed to recreate session: {reconnect_error}")
            else:
                print(f"❌ [{time_str}] Error checking {channel['name']}: {e}")
    
    async def reconnect_channels(self):
        """Reconnect to all channels after session recreation"""
        print("📡 Reconnecting to channels...")
        for channel in self.channels:
            try:
                # Handle invite link
                if 'joinchat' in channel['id'] or '+' in channel['id']:
                    # Extract invite hash from link
                    if '+' in channel['id']:
                        invite_hash = channel['id'].split('+')[-1]
                    else:
                        invite_hash = channel['id'].split('/')[-1]
                    
                    # Join channel using invite link
                    try:
                        result = await self.telegram_client.join_chat(invite_hash)
                        entity = result.chats[0]
                    except Exception as join_error:
                        print(f"⚠️ Could not join channel: {join_error}")
                        # Try to get entity directly
                        entity = await self.telegram_client.get_entity(channel['id'])
                else:
                    entity = await self.telegram_client.get_entity(channel['id'])
                
                channel['entity'] = entity
                
                # Get the latest message ID to start from
                messages = await self.telegram_client.get_messages(entity, limit=1)
                if messages:
                    channel['last_msg_id'] = messages[0].id
                
                print(f"✅ {channel['name']}: Reconnected")
                
            except Exception as e:
                print(f"❌ {channel['name']}: Failed to reconnect - {e}")
    
    async def start_monitoring(self):
        """Start real-time signal monitoring"""
        print("🚀 REAL-TIME SIGNAL MONITOR STARTING...")
        print(f"📄 CSV Files: Separate file for each channel")
        for channel_name, csv_file in self.csv_files.items():
            print(f"   📊 {channel_name}: {csv_file}")
        print("⚡ Monitoring: Every 1 second")
        print("🎯 Detection: Trading signals + Results")
        print("📊 Format: [time] NEW MESSAGE details")
        print("🚨 Alerts: Real-time signal notifications")
        print("-" * 60)
        
        # Initialize with authentication handling
        try:
            if not await self.initialize():
                print("❌ Failed to initialize - exiting")
                return
        except KeyboardInterrupt:
            print("\n🛑 Setup cancelled by user")
            return
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return
        
        print("✅ MONITORING ACTIVE - Watching for signals...")
        print("🔔 New messages will appear below:")
        print("=" * 60)
        
        self.running = True
        
        try:
            while self.running:
                # Check current channel
                channel = self.channels[self.current_channel]
                await self.check_channel(channel)
                
                # Move to next channel
                self.current_channel = (self.current_channel + 1) % len(self.channels)
                
                # Wait 1 second for real-time monitoring
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 MONITOR STOPPED BY USER")
            
            # Show session summary
            session_duration = datetime.now() - self.session_start
            duration_minutes = int(session_duration.total_seconds() / 60)
            duration_seconds = int(session_duration.total_seconds() % 60)
            
            print("\n📊 SESSION SUMMARY:")
            print(f"   ⏰ Duration: {duration_minutes}m {duration_seconds}s")
            print(f"   📨 Messages Processed: {self.messages_processed}")
            print(f"   🎯 Signals Detected: {self.signals_detected}")
            print(f"   📄 CSV Files:")
            for channel_name, csv_file in self.csv_files.items():
                print(f"      📊 {channel_name}: {csv_file}")
            print("📊 Session completed successfully")
        except Exception as e:
            print(f"\n❌ Monitor error: {e}")
            print("🔄 Restarting in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            self.running = False
            if self.telegram_client:
                try:
                    await self.telegram_client.disconnect()
                    print("🔌 Disconnected from Telegram")
                except:
                    pass

async def main():
    monitor = SimpleMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())