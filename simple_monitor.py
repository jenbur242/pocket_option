#!/usr/bin/env python3
"""
Simple Monitor - Fetch messages from Telegram channel and save to CSV
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
        
        # New channel to monitor
        self.channels = [
            {
                'id': 'https://t.me/+ZuCrnz2Yv99lNTg5',
                'name': 'james martin vip channel m1',
                'entity': None,
                'last_msg_id': None
            }
        ]
        
        # CSV file setup
        today = datetime.now().strftime('%Y%m%d')
        self.csv_file = f"/Users/raushankumar/Downloads/PocketOptionAPI/pocketoption_messages_{today}.csv"
        
        # Ensure CSV has headers
        self.ensure_csv_headers()
        
        self.current_channel = 0
        self.running = False
        
        # Session statistics
        self.session_start = datetime.now()
        self.signals_detected = 0
        self.messages_processed = 0
        self.last_status_time = None
    
    def ensure_csv_headers(self):
        """Ensure CSV file exists with proper headers"""
        headers = [
            'timestamp', 'channel', 'message_id', 'message_text', 
            'is_signal', 'asset', 'direction', 'signal_time'
        ]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
        
        # Check if file exists and has headers
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            print(f"📄 Created CSV file: {self.csv_file}")
        else:
            print(f"📄 Using existing CSV file: {self.csv_file}")
    
    async def initialize(self):
        """Initialize clients with session check and authentication"""
        try:
            print("🔌 Initializing Telegram connection...")
            
            # Clean any existing session files first to avoid database locks
            session_files = ['working_session.session', 'working_session.session-journal', 'working_session.session-wal']
            for session_file in session_files:
                if os.path.exists(session_file):
                    try:
                        os.remove(session_file)
                        print(f"🧹 Cleaned: {session_file}")
                    except Exception as e:
                        print(f"⚠️ Could not remove {session_file}: {e}")
            
            # Create fresh Telegram client
            self.telegram_client = TelegramClient('working_session', self.api_id, self.api_hash)
            
            print("📱 Creating fresh session...")
            await self.authenticate_new_session()
            
            # Test connection
            me = await self.telegram_client.get_me()
            print(f"✅ Logged in as: {me.first_name} ({me.phone})")
            
            # Get entities for all channels
            print("📡 Connecting to channels...")
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
    
    
    def extract_signal_data(self, message_text):
        """Extract signal data from message"""
        if not message_text:
            return None
        
        # Skip obvious non-signal messages
        skip_words = ['win', 'loss', '💔', '✅', 'register', 'code', 'bonus', 'join', 'channel', 'withdraw', 'verify', 'account']
        if any(skip_word in message_text.lower() for skip_word in skip_words):
            # But allow if it has VIP SIGNAL
            if 'VIP SIGNAL' not in message_text:
                return None
        
        # Must have VIP SIGNAL or signal indicators
        if not any(indicator in message_text for indicator in ['VIP SIGNAL', '💳', '🔥', '⌛', 'CALL', 'PUT']):
            return None
        
        # Extract Asset - try multiple patterns
        asset = None
        asset_patterns = [
            r'\*\*([A-Z]{6})-?OTC[p]?\*\*',  # **NZDUSD-OTC**
            r'💳\s*([A-Z]{6})-?OTC[p]?',     # 💳 AUDCAD-OTC or AUDCAD-OTCp
            r'💳\s*([A-Z]{6})\s',            # 💳 AUDCAD 
            r'([A-Z]{6})-OTC[p]?',           # AUDCAD-OTC or AUDCAD-OTCp
            r'�\s*([AA-Z]{3}[A-Z]{3})',      # � AUDCACD
            r'📊\s*([A-Z]{6})-?OTC[p]?',     # 📊 AUDCAD-OTC
        ]
        
        for pattern in asset_patterns:
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
            r'-\s*(\d{1,2}:\d{2})\s*$',        # - 21:32 at end
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
        """Save message to CSV file"""
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Prepare row data
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                channel_name = channel['name']
                message_id = message.id
                message_text = message.text.replace('\n', ' ').replace('\r', ' ')
                
                if signal_data:
                    is_signal = 'Yes'
                    asset = signal_data['asset']
                    direction = signal_data['direction']
                    signal_time = signal_data['signal_time'] or ''
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
                    
                    # Check if it's a signal with detailed analysis
                    signal_data = self.extract_signal_data(msg.text)
                    
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
                        if any(word in msg.text.lower() for word in ['win', 'result', '✅', 'confirmed']):
                            save_status = "📊 RESULT SAVED" if saved else "❌ SAVE FAILED"
                            print(f"   📊 RESULT MESSAGE: {save_status}")
                        else:
                            save_status = "📝 MESSAGE SAVED" if saved else "❌ SAVE FAILED"
                            print(f"   📝 Status: {save_status}")
                    
                    print(f"   📄 CSV: {self.csv_file}")
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
                    session_files = ['working_session.session', 'working_session.session-journal', 'working_session.session-wal']
                    for session_file in session_files:
                        if os.path.exists(session_file):
                            try:
                                os.remove(session_file)
                            except:
                                pass
                    
                    # Recreate client
                    self.telegram_client = TelegramClient('working_session', self.api_id, self.api_hash)
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
        print(f"📄 CSV File: {self.csv_file}")
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
                
                # Move to next channel (only one channel now, but keeping structure)
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
            print(f"   📄 CSV File: {self.csv_file}")
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