import asyncio
import os
import json
import logging
from telethon import TelegramClient, events, errors
from telethon.errors import SessionPasswordNeededError, UserDeactivatedBanError
from telethon.tl.functions.messages import GetHistoryRequest, DeleteHistoryRequest
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

# Updated Auto-Reply Message (Your Provided Message)
AUTO_REPLY_MESSAGE = """
This Id Working For Otp Wallah
[ https://t.me/otpsellers4 ]

This Powerful Ads Running By @OrbitService 

Ads Hosted by @OrbitService 

Shop : @OrbitShoppy 

Proofs @LegitProofs99

[ Message To @OrbitService Only For Run Ads And Buy Telegram And WhatsApp Accounts.. For Other All Otp's Msge to [ https://t.me/otpsellers4  ] Otp Wallah

Thanks For Msge To Us..
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

async def auto_reply(client, session_name, stop_event):
    """Auto-reply to private messages and fully delete the chat."""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private and not stop_event.is_set():
            try:
                # Reply to the message
                await event.reply(AUTO_REPLY_MESSAGE)
                logging.info(f"Replied to {event.sender_id} in session {session_name}")

                # Fully delete the chat history
                await client(DeleteHistoryRequest(peer=event.sender_id, max_id=0, revoke=False))
                logging.info(f"Fully deleted chat with {event.sender_id} in session {session_name}")
                print(Fore.GREEN + f"Fully deleted chat with {event.sender_id} in session {session_name}")

            except errors.FloodWaitError as e:
                print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logging.error(f"Failed to reply or delete chat with {event.sender_id}: {str(e)}")
                print(Fore.RED + f"Failed to reply or delete chat with {event.sender_id}: {str(e)}")

async def forward_messages_to_groups(client, last_message, session_name, group):
    """Forwards a message to a specific group using the given session."""
    try:
        await client.forward_messages(group, last_message)
        print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
        logging.info(f"Message forwarded to {group.title} using {session_name}")
    except errors.FloodWaitError as e:
        print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
        await asyncio.sleep(e.seconds)
    except errors.PeerIdInvalidError:
        print(Fore.RED + f"Skipping invalid group: {group.title}")
        logging.warning(f"Skipping invalid group: {group.title}")
    except Exception as e:
        logging.error(f"Failed to forward message to {group.title}: {str(e)}")
        print(Fore.RED + f"Failed to forward message to {group.title}: {str(e)}")

async def login_and_execute(api_id, api_hash, phone_number, session_name, delay_between_accounts, index):
    """Handles login and executes forwarding + auto-reply with delayed starts."""
    stop_event = asyncio.Event()
    client = TelegramClient(session_name, api_id, api_hash)

    # Delay start based on index
    if index > 0:
        print(Fore.CYAN + f"\nWaiting {delay_between_accounts} seconds before starting session {session_name}...")
        await asyncio.sleep(delay_between_accounts * index)

    try:
        await client.start(phone=phone_number)

        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            while True:
                otp = input(Fore.CYAN + f"Enter the OTP for {phone_number}: ")
                try:
                    await client.sign_in(phone_number, otp)
                    break
                except errors.PhoneCodeInvalidError:
                    print(Fore.RED + "Invalid OTP. Please try again.")
                except errors.PhoneCodeExpiredError:
                    print(Fore.RED + "OTP expired. Resending code...")
                    await client.send_code_request(phone_number)

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
            print(Fore.RED + "No messages found in 'Saved Messages'. Skipping this session.")
            return

        last_message = history.messages[0]

        # Start auto-reply in the background
        print(Fore.CYAN + f"Starting auto-reply for session {session_name}...")
        asyncio.create_task(auto_reply(client, session_name, stop_event))

        return client, last_message

    except UserDeactivatedBanError:
        print(Fore.RED + f"Account {session_name} is banned. Skipping this session.")
    except Exception as e:
        print(Fore.RED + f"Unexpected error in session {session_name}: {str(e)}")
    return None, None

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

        # Step 2: Ask for delay between accounts
        delay_between_accounts = int(input("Enter delay (in seconds) between each account's start: "))

        # Step 3: Login to all accounts and prepare clients
        clients = []
        for index, session in enumerate(active_sessions):
            api_id, api_hash, phone_number, session_name = session
            client, last_message = await login_and_execute(api_id, api_hash, phone_number, session_name, delay_between_accounts, index)
            if client and last_message:
                clients.append((client, last_message, session_name))

        if not clients:
            print(Fore.RED + "No valid sessions available. Exiting.")
            return

        # Step 4: Forward messages to groups in a round-robin fashion
        while True:
            for client, last_message, session_name in clients:
                async for dialog in client.iter_dialogs():
                    if dialog.is_group:
                        group = dialog.entity
                        await forward_messages_to_groups(client, last_message, session_name, group)
                        await asyncio.sleep(delay_between_accounts)  # Delay between accounts

    except ValueError:
        print(Fore.RED + "Invalid input. Please enter a valid number.")
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nProcess interrupted by the user.")

if __name__ == "__main__":
    asyncio.run(main())
