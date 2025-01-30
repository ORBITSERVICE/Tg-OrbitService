import asyncio
import os
import json
import random
import logging
from telethon import TelegramClient, events, errors
from telethon.errors import SessionPasswordNeededError, UserDeactivatedBanError
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

# Updated Auto-Reply Message
AUTO_REPLY_MESSAGE = """
🤠 Please message @OrbitService for inquiries.
❤️ STORE: @ORBITSHOPPY  
❤️ PROOFS: @LEGITPROOFS99  
😎 DM: @ORBITSERVICE for deals
"""

def display_banner():
    """Display the banner using pyfiglet."""
    print(Fore.RED + pyfiglet.figlet_format("Og_Flame"))
    print(Fore.GREEN + "Made by @Og_Flame\n")

# Function to save session credentials
def save_credentials(session_name, credentials):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, "w") as f:
        json.dump(credentials, f)

# Function to load session credentials
def load_credentials(session_name):
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
        print(Fore.RED + f"Failed to retrieve saved messages: {str(e)}")
        logging.error(f"Failed to retrieve saved messages: {str(e)}")
        return None

async def forward_messages_to_groups(client, last_message, session_name, rounds, delay_between_rounds):
    """Forward the last saved message to all groups."""
    try:
        group_dialogs = [dialog for dialog in await client.get_dialogs() if dialog.is_group]

        if not group_dialogs:
            print(Fore.RED + f"No groups found for session {session_name}.")
            logging.warning(f"No groups found for session {session_name}.")
            return

        for round_num in range(1, rounds + 1):
            print(Fore.YELLOW + f"\nStarting round {round_num} for session {session_name}...")
            for dialog in group_dialogs:
                group = dialog.entity
                try:
                    await client.forward_messages(group, last_message)
                    print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
                    logging.info(f"Message forwarded to {group.title} using {session_name}")
                except errors.FloodWaitError as e:
                    print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
                    logging.warning(f"Rate limit exceeded for {group.title}. Waiting for {e.seconds} seconds.")
                    await asyncio.sleep(e.seconds)
                    continue
                except Exception as e:
                    print(Fore.RED + f"Failed to forward message to {group.title}: {str(e)}")
                    logging.error(f"Failed to forward message to {group.title}: {str(e)}")

                # Reduced delay to 5-10 seconds
                delay = random.randint(5, 10)
                print(f"Waiting for {delay} seconds before forwarding to the next group...")
                await asyncio.sleep(delay)

            print(Fore.GREEN + f"Round {round_num} completed for session {session_name}.")
            if round_num < rounds:
                print(Fore.CYAN + f"Waiting for {delay_between_rounds} seconds before next round...")
                await asyncio.sleep(delay_between_rounds)
    except Exception as e:
        print(Fore.RED + f"Unexpected error in forward_messages_to_groups: {str(e)}")
        logging.error(f"Unexpected error in forward_messages_to_groups: {str(e)}")

async def auto_reply(client, session_name):
    """Auto-reply to private messages."""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                print(Fore.GREEN + f"Replied to {event.sender_id} in session {session_name}")
                logging.info(f"Replied to {event.sender_id} in session {session_name}")
            except errors.FloodWaitError as e:
                print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
                logging.warning(f"Rate limit exceeded for {event.sender_id}. Waiting for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                print(Fore.RED + f"Failed to reply to {event.sender_id}: {str(e)}")
                logging.error(f"Failed to reply to {event.sender_id}: {str(e)}")

    await client.run_until_disconnected()

async def main():
    """Main function to handle user input and execute the script."""
    display_banner()

    try:
        num_sessions = int(input("Enter the number of sessions: "))
        if num_sessions <= 0:
            print(Fore.RED + "Number of sessions must be greater than 0.")
            return

        clients = []

        for i in range(1, num_sessions + 1):
            session_name = f"session{i}"
            credentials = load_credentials(session_name)

            if credentials:
                print(Fore.GREEN + f"\nUsing saved credentials for session {i}.")
                api_id = credentials["api_id"]
                api_hash = credentials["api_hash"]
                phone_number = credentials["phone_number"]
            else:
                print(Fore.YELLOW + f"\nEnter details for account {i}:")
                api_id = int(input(Fore.CYAN + f"Enter API ID for session {i}: "))
                api_hash = input(Fore.CYAN + f"Enter API hash for session {i}: ")
                phone_number = input(Fore.CYAN + f"Enter phone number for session {i}: ")

                credentials = {
                    "api_id": api_id,
                    "api_hash": api_hash,
                    "phone_number": phone_number,
                }
                save_credentials(session_name, credentials)

            client = TelegramClient(session_name, api_id, api_hash)
            await client.start(phone=phone_number)
            clients.append(client)

        print(Fore.MAGENTA + "\nChoose an option:")
        print(Fore.YELLOW + "1. Auto Forwarding (Forward last saved message to all groups)")
        print(Fore.YELLOW + "2. Auto Reply (Reply to private messages)")

        option = int(input(Fore.CYAN + "Enter your choice: "))
        rounds, delay_between_rounds = 0, 0

        if option == 1:
            rounds = int(input(Fore.MAGENTA + "How many rounds should the message be sent? "))
            delay_between_rounds = int(input(Fore.MAGENTA + "Enter delay (in seconds) between rounds: "))
            print(Fore.GREEN + "Starting Auto Forwarding...")

            for client in clients:
                last_message = await get_last_saved_message(client)
                if last_message:
                    await forward_messages_to_groups(client, last_message, client.session.filename, rounds, delay_between_rounds)
        elif option == 2:
            print(Fore.GREEN + "Starting Auto Reply...")
            for client in clients:
                await auto_reply(client)
        else:
            print(Fore.RED + "Invalid option selected.")

        for client in clients:
            await client.disconnect()

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript terminated by user.")
    except Exception as e:
        print(Fore.RED + f"Error: {str(e)}")
        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
