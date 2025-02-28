import asyncio
import os
import json
import logging
from telethon import TelegramClient, events, errors
from telethon.errors import UserDeactivatedBanError
from telethon.tl.functions.messages import GetHistoryRequest, DeleteHistoryRequest
from colorama import init, Fore
import pyfiglet

init(autoreset=True)

CREDENTIALS_FOLDER = 'sessions'

if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

logging.basicConfig(
    filename='og_flame_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

AUTO_REPLY_MESSAGE = """
This Id Working For Otp Wallah
[ https://t.me/otpsellers4 ]

This Powerful Ads Running By @OrbitService 

Shop : @OrbitShoppy 

Proofs @LegitProofs99

[ Message To @OrbitService Only For Run Ads And Buy Telegram And WhatsApp Accounts.. For Other All Otp's Msge to [ https://t.me/otpsellers4  ] Otp Wallah
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
    print(Fore.GREEN + "Made by @Og_Flame | @OrbitService\n")

async def auto_reply(client, session_name):
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                logging.info(f"Replied to {event.sender_id} in {session_name}")
                await client(DeleteHistoryRequest(peer=event.sender_id, max_id=0, revoke=False))
                print(Fore.GREEN + f"Deleted chat with {event.sender_id}")
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logging.error(f"Auto-Reply Error: {str(e)}")

async def forward_messages_to_groups(client, last_message, session_name, group):
    try:
        await client.send_message(group, last_message.message, link_preview=False)
        print(Fore.GREEN + f"Message Sent to {group.title} from {session_name}")

    except errors.FloodWaitError as e:
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logging.error(f"Forward Error: {str(e)}")

async def login_and_execute(api_id, api_hash, phone_number, session_name, delay_between_accounts, index):
    client = TelegramClient(session_name, api_id, api_hash)

    if index > 0:
        print(Fore.CYAN + f"Waiting {delay_between_accounts} seconds for {session_name}...")
        await asyncio.sleep(delay_between_accounts * index)

    try:
        await client.start(phone=phone_number)

        saved_peer = await client.get_input_entity('me')
        history = await client(GetHistoryRequest(peer=saved_peer, limit=1, offset_id=0, offset_date=None, add_offset=0, max_id=0, min_id=0, hash=0))

        if not history.messages:
            print(Fore.RED + f"No messages in Saved Messages for {session_name}")
            return None, None

        last_message = history.messages[0]

        asyncio.create_task(auto_reply(client, session_name))
        return client, last_message

    except UserDeactivatedBanError:
        print(Fore.RED + f"Session {session_name} is BANNED!")
    except Exception as e:
        print(Fore.RED + f"Error in {session_name}: {str(e)}")

    return None, None

async def main():
    display_banner()

    try:
        num_sessions = int(input("Enter Number of Sessions: "))
        active_sessions = []

        for i in range(1, num_sessions + 1):
            session_name = f'session{i}'
            credentials = load_credentials(session_name)

            if credentials:
                print(Fore.GREEN + f"Using Saved Login for {session_name}")
            else:
                print(Fore.CYAN + f"Setup {session_name}")
                api_id = int(input("API ID: "))
                api_hash = input("API Hash: ")
                phone_number = input("Phone Number (with +): ")
                credentials = {'api_id': api_id, 'api_hash': api_hash, 'phone_number': phone_number}
                save_credentials(session_name, credentials)

            active_sessions.append((credentials['api_id'], credentials['api_hash'], credentials['phone_number'], session_name))

        delay_between_accounts = int(input("Delay between Sessions (Seconds): "))

        clients = []
        for index, session in enumerate(active_sessions):
            api_id, api_hash, phone_number, session_name = session
            client, last_message = await login_and_execute(api_id, api_hash, phone_number, session_name, delay_between_accounts, index)
            if client:
                clients.append((client, last_message, session_name))

        while True:
            for client, last_message, session_name in clients:
                async for dialog in client.iter_dialogs():
                    if dialog.is_group:
                        await forward_messages_to_groups(client, last_message, session_name, dialog.entity)
                        await asyncio.sleep(delay_between_accounts)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nStopped by User")
    except ValueError:
        print(Fore.RED + "Invalid Number Input")

if __name__ == "__main__":
    asyncio.run(main())
