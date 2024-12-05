import asyncio
import os
import json
import random
import logging
from telethon import TelegramClient, errors
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import LeaveChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import init, Fore
import pyfiglet

# Initialize colorama for colored output
init(autoreset=True)

CREDENTIALS_FOLDER = 'sessions'

# Create a session folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Set up logging
logging.basicConfig(filename='orbit_service.log', level=logging.INFO, format='%(asctime)s - %(message)s')

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

# Function to display banner
def display_banner():
    print(Fore.RED + pyfiglet.figlet_format("OrbitService"))
    print(Fore.GREEN + "Made by @OrbitService\n")

# Function to forward messages to groups
async def forward_messages_to_groups(client, last_message, session_name):
    group_count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            group = dialog.entity
            try:
                # Try to forward the message to the group
                await client.forward_messages(group, last_message)
                print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
                logging.info(f"Message forwarded to {group.title} using {session_name}")
            except errors.FloodWaitError as e:
                # Handle rate-limiting error
                print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds before retrying.")
                logging.warning(f"Rate limit exceeded for {group.title}. Waiting for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
                continue
            except Exception as e:
                # Handle other errors (leave the group if forwarding failed)
                print(Fore.RED + f"Failed to forward message to {group.title}: {str(e)}")
                logging.error(f"Failed to forward message to {group.title}: {str(e)}")

            group_count += 1

            # Introduce a random delay between 15 to 30 seconds to reduce the chances of being banned
            delay = random.randint(15, 30)
            print(f"Waiting for {delay} seconds before forwarding to the next group...")
            await asyncio.sleep(delay)

            # Introduce a longer delay after every 10 to 15 groups
            if group_count % random.randint(10, 15) == 0:
                long_delay = random.randint(60, 120)
                print(f"Completed {group_count} groups. Waiting for {long_delay} seconds to reduce the risk of being banned...")
                await asyncio.sleep(long_delay)

# Function to login and forward messages
async def login_and_forward(api_id, api_hash, phone_number, session_name):
    client = TelegramClient(session_name, api_id, api_hash)

    await client.start(phone=phone_number)

    try:
        if await client.is_user_authorized() is False:
            await client.send_code_request(phone_number)
            await client.sign_in(phone_number)
    except SessionPasswordNeededError:
        password = input("Two-factor authentication enabled. Enter your password: ")
        await client.sign_in(password=password)

    saved_messages_peer = await client.get_input_entity('me')

    # Corrected GetHistoryRequest with missing arguments
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
        logging.warning(f"No messages found in 'Saved Messages' for session {session_name}")
        return

    last_message = history.messages[0]

    # Ask how many times and delay after login
    repeat_count = int(input(f"How many times do you want to send the message to all groups for {session_name}? "))
    delay_between_rounds = int(input(f"Enter the delay (in seconds) between each round for {session_name}: "))

    for round_num in range(1, repeat_count + 1):
        print(f"\nStarting round {round_num} of forwarding messages to all groups for {session_name}.")
        await forward_messages_to_groups(client, last_message, session_name)

        if round_num < repeat_count:
            print(f"Delaying for {delay_between_rounds} seconds before the next round.")
            await asyncio.sleep(delay_between_rounds)

    await client.disconnect()

# Function to leave unwanted groups (Removed as per your request)
async def leave_unwanted_groups(client):
    pass  # No longer needed, leaving groups is disabled

async def main():
    display_banner()

    # Load sessions and ask how many to log in
    num_sessions = int(input("Enter how many sessions you want to log in: "))
    tasks = []

    for i in range(1, num_sessions + 1):
        session_name = f'session{i}'
        credentials = load_credentials(session_name)

        if credentials:
            print(f"\nUsing saved credentials for session {i}.")
            api_id = credentials['api_id']
            api_hash = credentials['api_hash']
            phone_number = credentials['phone_number']
        else:
            print(f"\nEnter details for account {i}:")
            api_id = int(input(f"Enter API ID for session {i}: "))
            api_hash = input(f"Enter API hash for session {i}: ")
            phone_number = input(f"Enter phone number for session {i} (with country code): ")

            credentials = {
                'api_id': api_id,
                'api_hash': api_hash,
                'phone_number': phone_number
            }
            save_credentials(session_name, credentials)

        # Let user choose action
        choice = int(input(f"\nSelect action for session {i}:\n1. AutoSender\n2. Leave Groups\nEnter choice: "))
        if choice == 1:
            tasks.append(login_and_forward(api_id, api_hash, phone_number, session_name))
        elif choice == 2:
            print("Leaving groups feature is disabled in this version.")
            logging.info(f"Leave groups option selected for session {session_name}, but it is disabled.")

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
