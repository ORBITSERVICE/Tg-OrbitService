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

# Promotional Message (Added as per your request)
PROMO_MESSAGE = """
[All Items Under 1 Store]

Best Plan For Resellers

- All Type Of Telegram Automation Scripts (AutoForwarder, Auto replay without Premium, Group link checker, Auto Leaver, Grp to Grp adder) - DM @OrbitService for more plans

- Old And Fresh Telegram Numbers (+91) - DM @OrbitService for more plans

OTT
- NETFLIX 4K: 99₹/2$ (1 month) - DM @OrbitService for more plans

- PRIME 4K: 39₹/1$ (1 month) - DM @OrbitService for more plans

- JIOHOTSTAR 4K: 79₹/1$ (1 month) - DM @OrbitService for more plans

- SONYLIV/ZEE5: 39₹ each (1 month) - DM @OrbitService for more plans

- CRUNCHYROLL: 49₹/1$ (1 month) - DM @OrbitService for more plans

- YOUTUBE: 39₹/1$ (1 month) - DM @OrbitService for more plans

MUSIC
- SPOTIFY: 49₹/1$ (1 month) - DM @OrbitService for more plans
- APPLE MUSIC: 79₹/2$ (1 month) - DM @OrbitService for more plans

ADULT
- PHUB: 79₹/2$ (1 month) - DM @OrbitService for more plans
- FAPHOUSE: 89₹/2.5$ (1 month) - DM @OrbitService for more plans
- BRAZZERS: 79₹/2$ (1 month) - DM @OrbitService for more plans
- ONLYFANS: 100$ LOADED AT 299₹/8$ - DM @OrbitService for more plans

AI
- CHATGPT: 499₹/10$ (1 month) - DM @OrbitService for more plans
- PERPLEXITY AI: 899₹/20$ (1 year) - DM @OrbitService for more plans

VPN
- NORD VPN: 79₹/1.5$ (1 month) - DM @OrbitService for more plans
- EXPRESS VPN: 99₹/2$ (1 month) - DM @OrbitService for more plans
- HMA VPN: 279₹/5$ (1.5 years) - DM @OrbitService for more plans

Shopping
- Amazon Prime Membership: 499₹/10$ (1 year) - DM @OrbitService for more plans
- Flipkart Plus Membership: 299₹/5$ (1 year) - DM @OrbitService for more plans

Fitness
- Cult.fit Membership: 499₹/10$ (3 months) - DM @OrbitService for more plans

- Headspace Premium: 299₹/6$ (1 month) - DM @OrbitService for more plans

Editing
- CAPCUT: 399₹/7.5$ (3 months) - DM @OrbitService for more plans

- CANVA: 49₹/1.5$ (1 month) - DM @OrbitService for more plans

For other OTT platforms and subscriptions message @OrbitService

FOR PROOFS CHECK BIO @OrbitService 

Want to make money? We can help you earn min 1k per day with Telegram Marketing. DM @OrbitService for details.

For Resellers:
- YT 3M - DM @OrbitService for more plans

- YT FAM - DM @OrbitService for more plans

- PRIME 6M - DM @OrbitService for more plans

- JIO RECHARGE - DM @OrbitService for more plans
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
