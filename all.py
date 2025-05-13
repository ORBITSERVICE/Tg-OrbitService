import asyncio
import os
import json
import random
import logging
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.errors import (
    UserDeactivatedBanError,
    FloodWaitError,
    ChannelPrivateError,
    ChatWriteForbiddenError,
    ChannelInvalidError
)
from colorama import init, Fore
import pyfiglet

# Initialize colorama
init(autoreset=True)

# Configuration
CREDENTIALS_FOLDER = 'sessions'
os.makedirs(CREDENTIALS_FOLDER, exist_ok=True)
TARGET_CHANNEL = "https://t.me/OttMakershop"

# Performance Settings
MAX_CONCURRENT_SESSIONS = 10  # Increased to 10 concurrent sessions
MESSAGE_CHECK_LIMIT = 10
BASE_DELAY = 15
MAX_DELAY = 45

# Set up logging
logging.basicConfig(
    filename='orbit_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Auto-Reply Message
AUTO_REPLY_MESSAGE = "Dm @OrbitService"

def display_banner():
    """Display the banner"""
    print(Fore.RED + pyfiglet.figlet_format("ORBIT ADBOT"))
    print(Fore.GREEN + "By @OrbitService\n")

def save_credentials(session_name, credentials):
    """Save session credentials"""
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, "w") as f:
        json.dump(credentials, f)

def load_credentials(session_name):
    """Load session credentials"""
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

async def process_batch(sessions_batch):
    """Process a batch of sessions concurrently"""
    tasks = []
    for session_name, creds in sessions_batch:
        print(Fore.CYAN + f"\nPreparing {session_name}...")
        tasks.append(run_session(session_name, creds))
    await asyncio.gather(*tasks)

async def ensure_channel_joined(client, session_name):
    """Optimized channel joining with quick verification"""
    try:
        try:
            entity = await client.get_entity(TARGET_CHANNEL)
            # Quick check if already participant
            try:
                await client.get_permissions(entity)
                print(Fore.YELLOW + f"[{session_name}] Already in channel")
                return entity
            except ChannelPrivateError:
                pass
            
            await client(functions.channels.JoinChannelRequest(entity))
            print(Fore.GREEN + f"[{session_name}] Joined channel")
            return entity
        except FloodWaitError as e:
            wait = min(e.seconds, 60)  # Cap wait at 60 seconds
            print(Fore.YELLOW + f"[{session_name}] Flood wait: {wait} sec")
            await asyncio.sleep(wait)
            return await ensure_channel_joined(client, session_name)
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Join failed: {str(e)}")
        return None

async def get_last_channel_message(client):
    """Fast message fetching with quick validation"""
    try:
        entity = await client.get_entity(TARGET_CHANNEL)
        messages = await client.get_messages(entity, limit=MESSAGE_CHECK_LIMIT)
        for msg in messages:
            if not isinstance(msg, types.MessageService):
                return msg
        return None
    except Exception as e:
        print(Fore.RED + f"Message fetch error: {str(e)}")
        return None

async def forward_with_retry(client, entity, message, max_retries=2):
    """Optimized forwarding with quick retries"""
    for attempt in range(max_retries):
        try:
            await client.forward_messages(entity, message)
            return True
        except FloodWaitError as e:
            wait = min(e.seconds, 30)  # Cap at 30 seconds
            if attempt == max_retries - 1:
                raise
            print(Fore.YELLOW + f"Flood wait: {wait} sec (retry {attempt + 1})")
            await asyncio.sleep(wait)
        except (ChannelPrivateError, ChatWriteForbiddenError, ChannelInvalidError):
            return False
    return False

async def forward_message_to_groups(client, session_name, message):
    """Optimized group forwarding"""
    try:
        # Get only active group dialogs
        dialogs = [d for d in await client.get_dialogs() if d.is_group]
        
        if not dialogs:
            print(Fore.YELLOW + f"[{session_name}] No groups found")
            return

        print(Fore.CYAN + f"[{session_name}] Processing {len(dialogs)} groups")
        
        for dialog in dialogs:
            group = dialog.entity
            group_name = getattr(group, 'title', 'UNKNOWN')
            
            try:
                if await forward_with_retry(client, group, message):
                    print(Fore.GREEN + f"[{session_name}] Sent to {group_name}")
                else:
                    print(Fore.YELLOW + f"[{session_name}] No access to {group_name}")
                
                await asyncio.sleep(random.randint(BASE_DELAY, MAX_DELAY))
                
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Group error: {str(e)}")
                continue

    except Exception as e:
        print(Fore.RED + f"[{session_name}] Forwarding failed: {str(e)}")

async def setup_auto_reply(client, session_name):
    """Lightweight auto-reply setup"""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
            except FloodWaitError as e:
                await asyncio.sleep(min(e.seconds, 30))
                await event.reply(AUTO_REPLY_MESSAGE)
            except Exception:
                pass

async def run_session(session_name, credentials):
    """Optimized session runner"""
    client = None
    try:
        client = TelegramClient(
            StringSession(credentials["string_session"]),
            credentials["api_id"],
            credentials["api_hash"],
            device_model=f"OrbitBot-{random.randint(1000,9999)}",
            system_version="4.16.30-vxCustom",
            connection_retries=2,
            request_retries=2,
            auto_reconnect=True
        )
        
        await client.start()
        print(Fore.GREEN + f"[{session_name}] Ready")
        
        if not await ensure_channel_joined(client, session_name):
            return
            
        await setup_auto_reply(client, session_name)
        
        while True:
            try:
                msg = await get_last_channel_message(client)
                if msg:
                    await forward_message_to_groups(client, session_name, msg)
                await asyncio.sleep(900)  # 15 minute cycles
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Cycle error: {str(e)}")
                await asyncio.sleep(300)
                
    except UserDeactivatedBanError:
        print(Fore.RED + f"[{session_name}] Banned")
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Failed: {str(e)}")
    finally:
        if client:
            await client.disconnect()

async def main():
    """Optimized main flow"""
    display_banner()
    
    try:
        num_sessions = int(input("Enter number of sessions: "))
        if num_sessions <= 0:
            raise ValueError("Must be > 0")
                
        # Prepare all sessions first
        sessions = []
        for i in range(1, num_sessions + 1):
            session_name = f"session{i}"
            creds = load_credentials(session_name)
            
            if not creds:
                print(Fore.CYAN + f"\nEnter details for {session_name}:")
                creds = {
                    "api_id": int(input("API ID: ")),
                    "api_hash": input("API Hash: "),
                    "string_session": input("String Session: ")
                }
                save_credentials(session_name, creds)
                
            sessions.append((session_name, creds))

        # Process in optimized batches
        print(Fore.GREEN + f"\nStarting {len(sessions)} sessions in batches of {MAX_CONCURRENT_SESSIONS}...")
        for i in range(0, len(sessions), MAX_CONCURRENT_SESSIONS):
            batch = sessions[i:i + MAX_CONCURRENT_SESSIONS]
            await process_batch(batch)
            if i + MAX_CONCURRENT_SESSIONS < len(sessions):
                print(Fore.CYAN + f"\nPreparing next batch...")
                await asyncio.sleep(5)  # Brief pause between batches
        
    except ValueError as e:
        print(Fore.RED + f"Input error: {str(e)}")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nStopped by user")
    except Exception as e:
        print(Fore.RED + f"Fatal: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped")
