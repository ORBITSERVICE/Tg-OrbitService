import asyncio
import os
import json
import random
import logging
import socket
from telethon import TelegramClient, events, errors
from telethon.errors import SessionPasswordNeededError, UserDeactivatedBanError
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import init, Fore
import pyfiglet

# Initialize colorama for colored output
init(autoreset=True)

CREDENTIALS_FOLDER = 'sessions'

if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Set up logging
logging.basicConfig(
    filename='og_flame_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Updated Auto-Reply Message
AUTO_REPLY_MESSAGE = """
DM @OrbitService For Deals
DM @OrbitService For Deals
DM @OrbitService For Deals
DM @OrbitService For Deals

Join @OrbitShoppy
Join @OrbitShoppy
Join @OrbitShoppy
Join @OrbitShoppy
"""

def save_credentials(session_name, credentials):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, 'w') as f:
        json.dump(credentials, f)

def load_credentials(session_name):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def display_banner():
    print(Fore.RED + pyfiglet.figlet_format("Og_Flame"))
    print(Fore.GREEN + "Made by @Og_Flame\n")

async def auto_reply(client, session_name):
    """Auto-reply to private messages."""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                logging.info(f"Replied to {event.sender_id} in session {session_name}")
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logging.error(f"Failed to reply to {event.sender_id}: {str(e)}")

async def forward_messages_to_groups(client, last_message, session_name, rounds):
    """Forwards messages to groups for a set number of rounds."""
    for round_num in range(1, rounds + 1):
        print(Fore.YELLOW + f"\nStarting round {round_num} for session {session_name}...")

        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group = dialog.entity
                try:
                    await client.forward_messages(group, last_message)
                    print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
                    logging.info(f"Message forwarded to {group.title} using {session_name}")
                except errors.FloodWaitError as e:
                    print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    logging.error(f"Failed to forward message to {group.title}: {str(e)}")
                    print(Fore.RED + f"Failed to forward message to {group.title}: {str(e)}")
                
                await asyncio.sleep(random.randint(15, 30))  # Delay between messages

        print(Fore.GREEN + f"Round {round_num} completed for session {session_name}.")

async def login_and_execute(api_id, api_hash, phone_number, session_name, rounds, delay_between_accounts, index):
    """Handles login and executes forwarding + auto-reply with delayed starts."""
    
    # Delay start based on index
    if index > 0:
        print(Fore.CYAN + f"\nWaiting {delay_between_accounts} seconds before starting session {session_name}...")
        await asyncio.sleep(delay_between_accounts * index)

    client = TelegramClient(session_name, api_id, api_hash)

    try:
        await client.start(phone=phone_number)

        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            otp = input(Fore.CYAN + f"Enter the OTP for {phone_number}: ")
            await client.sign_in(phone_number, otp)

        # Fetch last saved message
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

        if not history.messages:
            print("No messages found in 'Saved Messages'")
            return

        last_message = history.messages[0]

        # Start both auto-reply and forwarding
        print(Fore.CYAN + f"Starting auto-reply for session {session_name}...")
        asyncio.create_task(auto_reply(client, session_name))  # Runs auto-reply in background

        print(Fore.CYAN + f"Starting message forwarding for session {session_name}...")
        await forward_messages_to_groups(client, last_message, session_name, rounds)

    except UserDeactivatedBanError:
        print(Fore.RED + f"Account {session_name} is banned. Skipping this session.")
    except Exception as e:
        print(Fore.RED + f"Unexpected error in session {session_name}: {str(e)}")
    finally:
        await client.disconnect()

async def main():
    display_banner()

    try:
        num_sessions = int(input("Enter how many sessions you want to log in: "))
        active_sessions = []

        # Step 1: Login to all accounts
        for i in range(1, num_sessions + 1):
            session_name = f'session{i}'
            credentials = load_credentials(session_name)

            if credentials:
                print(f"\nUsing saved credentials for session {i}.")
            else:
                print(f"\nEnter details for account {i}:")
                api_id = int(input(f"Enter API ID for session {i}: "))
                api_hash = input(f"Enter API hash for session {i}: ")
                phone_number = input(f"Enter phone number for session {i} (with country code): ")

                credentials = {'api_id': api_id, 'api_hash': api_hash, 'phone_number': phone_number}
                save_credentials(session_name, credentials)

            active_sessions.append((credentials['api_id'], credentials['api_hash'], credentials['phone_number'], session_name))

        # Step 2: Ask for rounds and delay
        rounds = int(input(f"How many times should each account forward messages? "))
        delay_between_accounts = int(input(f"Enter delay (in seconds) between each account's start: "))

        # Step 3: Run accounts in parallel but delay their start
        tasks = []
        for index, session in enumerate(active_sessions):
            api_id, api_hash, phone_number, session_name = session
            tasks.append(login_and_execute(api_id, api_hash, phone_number, session_name, rounds, delay_between_accounts, index))

        await asyncio.gather(*tasks)  # Run all accounts concurrently

    except ValueError:
        print(Fore.RED + "Invalid input. Please enter a valid number.")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nProcess interrupted by the user.")

if __name__ == "__main__":
    asyncio.run(main())