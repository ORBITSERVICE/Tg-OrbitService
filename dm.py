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
    ChannelInvalidError,
    PeerIdInvalidError
)
from colorama import init, Fore
import pyfiglet

# Initialize colorama
init(autoreset=True)

# Configuration
CREDENTIALS_FOLDER = 'sessions'
os.makedirs(CREDENTIALS_FOLDER, exist_ok=True)
TARGET_USER = "OrbitService"  # Target username for DM forwarding

# Timing Settings
MIN_DELAY = 15  # Minimum delay between groups (seconds)
MAX_DELAY = 30  # Maximum delay between groups (seconds)
CYCLE_DELAY = 900  # 15 minutes between full cycles (seconds)
MAX_CONCURRENT = 10  # Number of accounts to run simultaneously

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

async def get_last_dm_message(client, session_name):
    """Get last message from target user's DM"""
    try:
        entity = await client.get_entity(TARGET_USER)
        messages = await client.get_messages(entity, limit=10)
        
        for msg in messages:
            # Skip service messages and empty messages
            if not isinstance(msg, types.MessageService) and msg.message:
                return msg
                
        print(Fore.YELLOW + f"[{session_name}] No forwardable messages in DM")
        return None
        
    except PeerIdInvalidError:
        print(Fore.RED + f"[{session_name}] Not in DM with @{TARGET_USER}")
        return None
    except Exception as e:
        print(Fore.RED + f"[{session_name}] DM error: {str(e)}")
        return None

async def forward_to_group(client, group, message, session_name):
    """Reliable message forwarding with retries"""
    try:
        await client.forward_messages(group, message)
        print(Fore.GREEN + f"[{session_name}] Sent to {getattr(group, 'title', 'UNKNOWN')}")
        return True
    except FloodWaitError as e:
        wait = min(e.seconds, 30)  # Cap at 30 seconds
        print(Fore.YELLOW + f"[{session_name}] Flood wait: {wait}s")
        await asyncio.sleep(wait)
        return await forward_to_group(client, group, message, session_name)
    except (ChannelPrivateError, ChatWriteForbiddenError):
        print(Fore.YELLOW + f"[{session_name}] No access to group")
        return False
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Forward error: {str(e)}")
        return False

async def process_groups(client, session_name, message):
    """Process all groups with strict timing control"""
    try:
        dialogs = await client.get_dialogs()
        groups = [d.entity for d in dialogs if d.is_group]
        
        if not groups:
            print(Fore.YELLOW + f"[{session_name}] No groups found")
            return

        print(Fore.CYAN + f"[{session_name}] Processing {len(groups)} groups")
        
        for group in groups:
            start_time = asyncio.get_event_loop().time()
            
            await forward_to_group(client, group, message, session_name)
            
            # Calculate remaining delay time
            elapsed = asyncio.get_event_loop().time() - start_time
            remaining_delay = max(0, random.randint(MIN_DELAY, MAX_DELAY) - elapsed)
            
            if remaining_delay > 0:
                print(Fore.CYAN + f"[{session_name}] Waiting {remaining_delay:.1f}s")
                await asyncio.sleep(remaining_delay)
                
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Group error: {str(e)}")

async def setup_auto_reply(client, session_name):
    """Efficient auto-reply setup"""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private and event.sender_id != (await client.get_me()).id:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                print(Fore.GREEN + f"[{session_name}] Replied to DM")
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
            request_retries=2
        )
        
        await client.start()
        print(Fore.GREEN + f"[{session_name}] Ready")
        
        await setup_auto_reply(client, session_name)
        
        while True:
            try:
                message = await get_last_dm_message(client, session_name)
                if message:
                    await process_groups(client, session_name, message)
                
                print(Fore.YELLOW + f"[{session_name}] Cycle complete, waiting {CYCLE_DELAY//60}min")
                await asyncio.sleep(CYCLE_DELAY)
                
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Error: {str(e)}")
                await asyncio.sleep(300)  # 5 minute cooldown on errors
                
    except UserDeactivatedBanError:
        print(Fore.RED + f"[{session_name}] Banned")
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Fatal: {str(e)}")
    finally:
        if client:
            await client.disconnect()

async def main():
    """Optimized main execution with 10 concurrent sessions"""
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

        # Process in optimized batches
        print(Fore.GREEN + f"\nStarting {len(sessions)} sessions (10 concurrent)")
        
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
        async def start_session(session_name, creds):
            async with semaphore:
                await run_session(session_name, creds)
        
        await asyncio.gather(*[start_session(name, creds) for name, creds in sessions])
        
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