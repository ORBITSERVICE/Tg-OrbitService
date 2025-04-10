import asyncio
import os
import json
import random
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import UserDeactivatedBanError, FloodWaitError
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import init, Fore
import pyfiglet

# Initialize colorama for colored output
init(autoreset=True)

# Define session folder
CREDENTIALS_FOLDER = 'sessions'
os.makedirs(CREDENTIALS_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename='og_flame_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Auto-Reply Message
AUTO_REPLY_MESSAGE = """
🌟 *Welcome to OrbitService!* 🌟

📢 Admin Support: @OrbitService  
🛒 Explore Our Store: @OrbitShoppy  
🔍 See Proofs & Reviews: @OrbitRepss

💬 *Need help or have questions?*  
👉 We're here to assist you! Feel free to message us anytime.

🚀 *Ready to get started?*  
Check out our store for exclusive deals and services!

Thank you for choosing OrbitService! 😊
"""

def display_banner():
    """Display the banner using pyfiglet."""
    print(Fore.RED + pyfiglet.figlet_format("Og_Flame"))
    print(Fore.GREEN + "Made by @Og_Flame\n")

def save_credentials(session_name, credentials):
    """Save session credentials to file."""
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, "w") as f:
        json.dump(credentials, f)

def load_credentials(session_name):
    """Load session credentials from file."""
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

async def get_last_saved_message(client):
    """Retrieve the last message from 'Saved Messages'."""
    try:
        saved_messages_peer = await client.get_input_entity('me')
        history = await client(GetHistoryRequest(
            peer=saved_messages_peer,
            limit=1,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            max_id=0,
            min_id=0,
            hash=0
        ))
        return history.messages[0] if history.messages else None
    except Exception as e:
        logging.error(f"Failed to retrieve saved messages: {str(e)}")
        return None

async def forward_messages(client, session_name):
    """Forward the last saved message to all groups with random delays."""
    try:
        last_message = await get_last_saved_message(client)
        if not last_message:
            print(Fore.RED + f"No saved message found for {session_name}")
            return

        dialogs = await client.get_dialogs()
        group_dialogs = [dialog for dialog in dialogs if dialog.is_group]

        if not group_dialogs:
            print(Fore.YELLOW + f"No groups found for {session_name}")
            return

        print(Fore.CYAN + f"Found {len(group_dialogs)} groups for {session_name}")

        for dialog in group_dialogs:
            group = dialog.entity
            try:
                await client.forward_messages(group, last_message)
                print(Fore.GREEN + f"Message forwarded to {group.title}")
                logging.info(f"Message forwarded to {group.title}")
            except FloodWaitError as e:
                print(Fore.RED + f"Waiting {e.seconds} seconds (flood wait)")
                await asyncio.sleep(e.seconds)
                await client.forward_messages(group, last_message)
            except Exception as e:
                print(Fore.RED + f"Failed to forward to {group.title}: {str(e)}")

            delay = random.randint(15, 30)
            await asyncio.sleep(delay)

    except Exception as e:
        logging.error(f"Error in forwarding for {session_name}: {str(e)}")

async def auto_reply(client, session_name):
    """Set up auto-reply to private messages."""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                print(Fore.GREEN + f"Replied to {event.sender_id}")
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
                await event.reply(AUTO_REPLY_MESSAGE)
            except Exception as e:
                print(Fore.RED + f"Failed to reply: {str(e)}")

async def run_session(session_name, credentials):
    """Run a single session with both forwarding and auto-reply."""
    client = TelegramClient(
        StringSession(credentials["string_session"]),
        credentials["api_id"],
        credentials["api_hash"]
    )
    
    try:
        await client.start()
        print(Fore.GREEN + f"{session_name} started successfully")
        
        # Run both functions concurrently
        await asyncio.gather(
            auto_reply(client, session_name),
            continuous_forwarding(client, session_name)
        )
        
    except UserDeactivatedBanError:
        print(Fore.RED + f"{session_name} is banned")
    except Exception as e:
        print(Fore.RED + f"{session_name} error: {str(e)}")
    finally:
        await client.disconnect()

async def continuous_forwarding(client, session_name):
    """Continuous forwarding with 15-minute intervals."""
    while True:
        await forward_messages(client, session_name)
        print(Fore.YELLOW + f"{session_name} waiting 15 minutes...")
        await asyncio.sleep(900)  # 15 minutes

async def main():
    """Main function to handle user input and execute the script."""
    display_banner()

    try:
        num_sessions = int(input("Enter number of sessions: "))
        if num_sessions <= 0:
            print(Fore.RED + "At least 1 session required")
            return

        tasks = []
        
        for i in range(1, num_sessions + 1):
            session_name = f"session{i}"
            credentials = load_credentials(session_name)

            if not credentials:
                print(Fore.CYAN + f"\nEnter details for {session_name}:")
                credentials = {
                    "api_id": int(input("API ID: ")),
                    "api_hash": input("API Hash: "),
                    "string_session": input("String Session: ")
                }
                save_credentials(session_name, credentials)

            tasks.append(run_session(session_name, credentials))

        print(Fore.GREEN + "\nStarting all sessions...")
        await asyncio.gather(*tasks)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nStopped by user")
    except Exception as e:
        print(Fore.RED + f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped")
