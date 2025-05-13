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

# Timing Settings
MIN_DELAY = 15  # Minimum delay between groups
MAX_DELAY = 30  # Maximum delay between groups
CYCLE_DELAY = 900  # 15 minutes between cycles

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

async def ensure_channel_joined(client, session_name):
    """Ensure joined to target channel with quick verification"""
    try:
        entity = await client.get_entity(TARGET_CHANNEL)
        try:
            # Quick check if already participant
            await client.get_permissions(entity)
            print(Fore.YELLOW + f"[{session_name}] Already in channel")
            return entity
        except ChannelPrivateError:
            try:
                await client(functions.channels.JoinChannelRequest(entity))
                print(Fore.GREEN + f"[{session_name}] Joined channel")
                return entity
            except FloodWaitError as e:
                print(Fore.YELLOW + f"[{session_name}] Flood wait: {e.seconds}s")
                await asyncio.sleep(e.seconds)
                return await ensure_channel_joined(client, session_name)
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Channel error: {str(e)}")
        return None

async def get_last_channel_message(client):
    """Get last non-service message from channel"""
    try:
        entity = await client.get_entity(TARGET_CHANNEL)
        messages = await client.get_messages(entity, limit=10)
        for msg in messages:
            if not isinstance(msg, types.MessageService):
                return msg
        return None
    except Exception as e:
        print(Fore.RED + f"Message error: {str(e)}")
        return None

async def forward_to_group(client, group, message, session_name):
    """Forward message to single group with error handling"""
    try:
        await client.forward_messages(group, message)
        print(Fore.GREEN + f"[{session_name}] Sent to {getattr(group, 'title', 'UNKNOWN')}")
        return True
    except FloodWaitError as e:
        print(Fore.YELLOW + f"[{session_name}] Flood wait: {e.seconds}s")
        await asyncio.sleep(e.seconds)
        return await forward_to_group(client, group, message, session_name)
    except (ChannelPrivateError, ChatWriteForbiddenError):
        print(Fore.YELLOW + f"[{session_name}] No access to group")
        return False
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Forward error: {str(e)}")
        return False

async def process_groups(client, session_name, message):
    """Process all groups with proper delays"""
    try:
        dialogs = await client.get_dialogs()
        groups = [d.entity for d in dialogs if d.is_group]
        
        if not groups:
            print(Fore.YELLOW + f"[{session_name}] No groups found")
            return

        print(Fore.CYAN + f"[{session_name}] Found {len(groups)} groups")
        
        for group in groups:
            await forward_to_group(client, group, message, session_name)
            delay = random.randint(MIN_DELAY, MAX_DELAY)
            print(Fore.CYAN + f"[{session_name}] Waiting {delay}s...")
            await asyncio.sleep(delay)
            
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Group processing error: {str(e)}")

async def setup_auto_reply(client, session_name):
    """Set up auto-reply handler"""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                print(Fore.GREEN + f"[{session_name}] Replied to DM")
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                await event.reply(AUTO_REPLY_MESSAGE)
            except Exception:
                pass

async def run_session(session_name, credentials):
    """Main session runner"""
    client = None
    try:
        client = TelegramClient(
            StringSession(credentials["string_session"]),
            credentials["api_id"],
            credentials["api_hash"],
            device_model="Orbit AdBot",
            system_version="4.16.30-vxCustom"
        )
        
        await client.start()
        print(Fore.GREEN + f"[{session_name}] Started")
        
        # Join channel and setup
        if not await ensure_channel_joined(client, session_name):
            return
            
        await setup_auto_reply(client, session_name)
        
        # Main working loop
        while True:
            try:
                message = await get_last_channel_message(client)
                if message:
                    await process_groups(client, session_name, message)
                print(Fore.YELLOW + f"[{session_name}] Cycle complete, waiting {CYCLE_DELAY//60}min")
                await asyncio.sleep(CYCLE_DELAY)
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
                
    except UserDeactivatedBanError:
        print(Fore.RED + f"[{session_name}] Banned")
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Fatal error: {str(e)}")
    finally:
        if client:
            await client.disconnect()

async def main():
    """Main execution flow"""
    display_banner()
    
    try:
        num_sessions = int(input("Enter number of sessions: "))
        if num_sessions <= 0:
            raise ValueError("Positive number required")
                
        # Prepare all sessions
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

        # Start all sessions with limited concurrency
        print(Fore.GREEN + "\nStarting all sessions...")
        semaphore = asyncio.Semaphore(5)  # Process 5 sessions at a time
        
        async def start_session(session_name, creds):
            async with semaphore:
                await run_session(session_name, creds)
        
        await asyncio.gather(*[start_session(name, creds) for name, creds in sessions])
        
    except ValueError as e:
        print(Fore.RED + f"Input error: {str(e)}")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nStopped by user")
    except Exception as e:
        print(Fore.RED + f"Fatal error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped")
