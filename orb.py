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

# Auto-Reply Message (Updated to just "Dm @OrbitService")
AUTO_REPLY_MESSAGE = "Dm @OrbitService"

# Promotional Message (Updated as per request)
PROMO_MESSAGE = """
ORBIT ADBOT SCRIPT

🎁 Introducing the Ultimate Telegram Automation Service!

⚡️ Are you tired of manually managing your Telegram groups?
⚡️ Looking for a fast, efficient, and affordable solution to forward messages, manage accounts, and streamline your workflow?

🔥 Here We Present:
The Most Advanced Telegram Automation Tool by @OrbitService

💡 Key Features:
- Auto Forward Messages: Send your saved messages to ALL your groups in just a few clicks.
- Smart Group Management: Automatically leave groups where messages can't be sent.
- Custom Rounds & Delays: Choose how many times to forward and set custom delays for maximum safety.
- Banned Account Handling: Seamlessly skip banned accounts and continue with active ones without interruptions.
- 24/7 Reliability: Runs non-stop until you manually stop it. Handles internet downtimes effortlessly!

📈 Why Choose Us?
- Lightning-fast performance.
- User-friendly and highly customizable.
- Designed to keep your accounts safe with built-in delay and error handling.
- Affordable Pricing for individuals and businesses alike!

✔️ Take control of your Telegram management like never before.
Join the growing community of professionals and businesses using @OrbitService's advanced tools.

❤️ Contact us today to get started!
Don't miss out - the future of Telegram automation is here.

✔️ Price just 499 INR / $10 (Non-negotiable) - Cheapest on Telegram!

⚠️ Special Feature: Auto Reply Without Premium

▶️ Contact: @OrbitService

👛 Payment Methods Accepted:
- UPI
- Crypto

👑 DM: @OrbitService
⚡️ Proof & Shop: Check Bio of @OrbitService
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

async def forward_promo_to_groups(client, session_name):
    """Forward the promotional message to all groups with random delays."""
    try:
        dialogs = await client.get_dialogs()
        group_dialogs = [dialog for dialog in dialogs if dialog.is_group]

        if not group_dialogs:
            print(Fore.YELLOW + f"[{session_name}] No groups found")
            return

        print(Fore.CYAN + f"[{session_name}] Found {len(group_dialogs)} groups")

        for dialog in group_dialogs:
            group = dialog.entity
            try:
                await client.send_message(group, PROMO_MESSAGE)
                print(Fore.GREEN + f"[{session_name}] Sent promo to {group.title}")
                logging.info(f"[{session_name}] Sent promo to {group.title}")
            except FloodWaitError as e:
                print(Fore.RED + f"[{session_name}] Flood wait: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                await client.send_message(group, PROMO_MESSAGE)
                print(Fore.GREEN + f"[{session_name}] Sent after wait to {group.title}")
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Failed to send to {group.title}: {str(e)}")
                logging.error(f"[{session_name}] Failed to send to {group.title}: {str(e)}")

            # Random delay between 15-30 seconds
            delay = random.randint(15, 30)
            print(Fore.CYAN + f"[{session_name}] Waiting {delay} seconds before next group...")
            await asyncio.sleep(delay)

    except Exception as e:
        print(Fore.RED + f"[{session_name}] Promo sending error: {str(e)}")
        logging.error(f"[{session_name}] Promo sending error: {str(e)}")

async def setup_auto_reply(client, session_name):
    """Set up auto-reply to private messages."""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                print(Fore.GREEN + f"[{session_name}] Replied to {event.sender_id}")
                logging.info(f"[{session_name}] Replied to {event.sender_id}")
            except FloodWaitError as e:
                print(Fore.RED + f"[{session_name}] Flood wait: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                await event.reply(AUTO_REPLY_MESSAGE)
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Failed to reply: {str(e)}")
                logging.error(f"[{session_name}] Failed to reply: {str(e)}")

async def run_session(session_name, credentials):
    """Run both promo sending and auto-reply for a session."""
    client = TelegramClient(
        StringSession(credentials["string_session"]),
        credentials["api_id"],
        credentials["api_hash"]
    )
    
    try:
        await client.start()
        print(Fore.GREEN + f"[{session_name}] Successfully logged in")
        
        # Start auto-reply
        await setup_auto_reply(client, session_name)
        
        # Continuous promo sending with 15 minute intervals
        while True:
            await forward_promo_to_groups(client, session_name)
            print(Fore.YELLOW + f"[{session_name}] Waiting 15 minutes before next round...")
            await asyncio.sleep(900)  # 15 minutes
            
    except UserDeactivatedBanError:
        print(Fore.RED + f"[{session_name}] Account banned")
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Error: {str(e)}")
    finally:
        await client.disconnect()

async def main():
    """Main function to handle user input and execute the script."""
    display_banner()

    try:
        num_sessions = int(input("Enter number of sessions: "))
        if num_sessions <= 0:
            print(Fore.RED + "Number must be greater than 0")
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

        print(Fore.GREEN + "\nStarting all sessions (Auto-Reply + Promo Sending)...")
        await asyncio.gather(*tasks)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped by user")
    except Exception as e:
        print(Fore.RED + f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped")
