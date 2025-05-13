import asyncio
import os
import json
import random
import logging
from telethon import TelegramClient, events, functions
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
TARGET_CHANNEL = "https://t.me/OttMakershop"  # Your channel link

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
    """Ensure the account is joined to target channel"""
    try:
        entity = await client.get_entity(TARGET_CHANNEL)
        try:
            await client(functions.channels.JoinChannelRequest(entity))
            print(Fore.GREEN + f"[{session_name}] Successfully joined channel")
        except FloodWaitError as e:
            print(Fore.YELLOW + f"[{session_name}] Flood wait: {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
            await ensure_channel_joined(client, session_name)
        except Exception as e:
            print(Fore.YELLOW + f"[{session_name}] Already in channel: {str(e)}")
        return entity
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Failed to join channel: {str(e)}")
        return None

async def get_last_channel_message(client):
    """Get the last message from target channel"""
    try:
        entity = await client.get_entity(TARGET_CHANNEL)
        messages = await client.get_messages(entity, limit=1)
        if messages:
            return messages[0]
        return None
    except Exception as e:
        print(Fore.RED + f"Error getting last message: {str(e)}")
        return None

async def forward_with_retry(client, entity, message, max_retries=3):
    """Forward message with retry logic"""
    for attempt in range(max_retries):
        try:
            await client.forward_messages(entity, message)
            return True
        except FloodWaitError as e:
            wait = e.seconds
            if attempt == max_retries - 1:
                raise
            print(Fore.YELLOW + f"Flood wait: {wait} seconds (attempt {attempt + 1}/{max_retries})")
            await asyncio.sleep(wait)
        except (ChannelPrivateError, ChatWriteForbiddenError, ChannelInvalidError):
            return False
    return False

async def forward_message_to_groups(client, session_name, message):
    """Improved forwarding with complete error handling"""
    try:
        dialogs = await client.get_dialogs()
        valid_groups = []
        
        # First pass: Filter valid groups
        for dialog in dialogs:
            if dialog.is_group:
                try:
                    # Verify we can access the group
                    await client.get_permissions(dialog.entity)
                    valid_groups.append(dialog)
                except Exception as e:
                    print(Fore.YELLOW + f"[{session_name}] Skipping inaccessible group: {str(e)}")
                    continue

        if not valid_groups:
            print(Fore.YELLOW + f"[{session_name}] No accessible groups found")
            return

        print(Fore.CYAN + f"[{session_name}] Found {len(valid_groups)} valid groups")

        for dialog in valid_groups:
            group = dialog.entity
            group_name = getattr(group, 'title', 'UNKNOWN_GROUP')
            
            try:
                success = await forward_with_retry(client, group, message)
                if success:
                    print(Fore.GREEN + f"[{session_name}] Forwarded to {group_name}")
                    logging.info(f"Successfully forwarded to {group_name}")
                else:
                    print(Fore.YELLOW + f"[{session_name}] Cannot forward to {group_name} (no permission)")
                    
                # Random delay with increasing variance
                base_delay = 15
                variance = min(60, len(valid_groups) // 2)  # More groups = more variance
                delay = random.randint(base_delay, base_delay + variance)
                print(Fore.CYAN + f"[{session_name}] Waiting {delay} seconds...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Critical error with {group_name}: {str(e)}")
                logging.error(f"Critical forwarding error: {str(e)}")
                continue

    except Exception as e:
        print(Fore.RED + f"[{session_name}] Fatal forwarding error: {str(e)}")
        logging.error(f"Fatal forwarding error: {str(e)}")

async def setup_auto_reply(client, session_name):
    """Auto-reply with improved error handling"""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                print(Fore.GREEN + f"[{session_name}] Replied to {event.sender_id}")
            except FloodWaitError as e:
                print(Fore.RED + f"[{session_name}] Flood wait: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                await event.reply(AUTO_REPLY_MESSAGE)
            except Exception as e:
                print(Fore.YELLOW + f"[{session_name}] Couldn't reply: {str(e)}")

async def run_session(session_name, credentials):
    """Session runner with full error recovery"""
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
        print(Fore.GREEN + f"[{session_name}] Successfully logged in")
        
        # Join channel if not already member
        channel_entity = await ensure_channel_joined(client, session_name)
        if not channel_entity:
            print(Fore.RED + f"[{session_name}] Could not access channel, skipping session")
            return
            
        # Update entity cache
        await client.get_dialogs()
        
        # Start services
        await setup_auto_reply(client, session_name)
        
        # Main forwarding loop
        while True:
            try:
                # Get fresh message each cycle
                message = await get_last_channel_message(client)
                if not message:
                    print(Fore.YELLOW + f"[{session_name}] No message found in channel")
                    await asyncio.sleep(300)
                    continue
                    
                await forward_message_to_groups(client, session_name, message)
                print(Fore.YELLOW + f"[{session_name}] Cycle completed, waiting 15 minutes...")
                await asyncio.sleep(900)
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Cycle error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes after error
                
    except UserDeactivatedBanError:
        print(Fore.RED + f"[{session_name}] Account banned")
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Fatal error: {str(e)}")
    finally:
        if client:
            await client.disconnect()

async def main():
    """Main execution flow"""
    display_banner()
    
    try:
        # Get number of sessions
        num_sessions = int(input("Enter number of sessions: "))
        if num_sessions <= 0:
            raise ValueError("Must be positive number")
                
        # Process all sessions
        tasks = []
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
                
            tasks.append(run_session(session_name, creds))
                
        print(Fore.GREEN + "\nStarting all sessions...")
        await asyncio.gather(*tasks)
        
    except ValueError as e:
        print(Fore.RED + f"Input error: {str(e)}")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nOperation cancelled by user")
    except Exception as e:
        print(Fore.RED + f"Fatal error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped")