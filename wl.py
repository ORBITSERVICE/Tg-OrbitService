import os
import time
import json
import asyncio
import random
from telethon import TelegramClient, events, errors
from telethon.errors import SessionPasswordNeededError, UserDeactivatedBanError
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import Fore, init
import pyfiglet

# Initialize colorama for colorful outputs
init(autoreset=True)

CREDENTIALS_FOLDER = "sessions"
AUTO_REPLY_MESSAGE = """
Please Message to @Og_Flame For Deals.
This is an Automated Message from @Og_Flame Telegram Automation Script.
"""

# Create the sessions folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Save session credentials
def save_credentials(session_name, credentials):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, "w") as f:
        json.dump(credentials, f)

# Load session credentials
def load_credentials(session_name):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

# Display banner
def display_banner():
    print(Fore.RED + pyfiglet.figlet_format("Og_Flame"))
    print(Fore.GREEN + "Made by @Og_Flame\n")

# Auto-forward messages to groups
async def forward_messages_to_groups(client, last_message, session_name, rounds, delay_between_rounds):
    for round_num in range(1, rounds + 1):
        print(Fore.YELLOW + f"\nStarting round {round_num} for session {session_name}...")
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                group = dialog.entity
                try:
                    await client.forward_messages(group, last_message)
                    print(Fore.GREEN + f"Message forwarded to {group.title} using {session_name}")
                except errors.FloodWaitError as e:
                    print(Fore.RED + f"Rate limit exceeded. Waiting for {e.seconds} seconds.")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    print(Fore.RED + f"Failed to forward message to {group.title}: {e}")
                delay = random.randint(15, 30)
                print(f"Waiting {delay} seconds before the next group...")
                await asyncio.sleep(delay)
        print(Fore.GREEN + f"Round {round_num} completed for session {session_name}.")
        if round_num < rounds:
            print(Fore.CYAN + f"Waiting {delay_between_rounds} seconds before the next round...")
            await asyncio.sleep(delay_between_rounds)

# Auto-reply to incoming private messages
async def auto_reply(client, session_name):
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            await event.reply(AUTO_REPLY_MESSAGE)
            print(Fore.GREEN + f"Replied to message from {event.sender_id} in session {session_name}")

    # Run the client indefinitely to listen for messages
    await client.run_until_disconnected()

# Login and run auto-forward and auto-reply simultaneously
async def login_and_execute(api_id, api_hash, phone_number, session_name):
    client = TelegramClient(session_name, api_id, api_hash)

    try:
        await client.start(phone=phone_number)

        if not await client.is_user_authorized():
            try:
                await client.send_code_request(phone_number)
                print(Fore.YELLOW + f"OTP sent to {phone_number}")
                otp = input(Fore.CYAN + f"Enter the OTP for {phone_number}: ")
                await client.sign_in(phone_number, otp)
            except SessionPasswordNeededError:
                password = input("Two-factor authentication enabled. Enter your password: ")
                await client.sign_in(password=password)

        print(Fore.GREEN + f"Logged in successfully for session {session_name}")

        # Load the last message from saved messages
        saved_messages_peer = await client.get_input_entity("me")
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
            print(Fore.RED + f"No messages found in 'Saved Messages' for session {session_name}")
            return

        last_message = history.messages[0]
        rounds = int(input(Fore.MAGENTA + f"How many times to forward messages for {session_name}? "))
        delay_between_rounds = int(input(Fore.MAGENTA + f"Delay between rounds (seconds) for {session_name}: "))

        # Run both auto-forwarding and auto-reply concurrently
        tasks = [
            asyncio.create_task(forward_messages_to_groups(client, last_message, session_name, rounds, delay_between_rounds)),
            asyncio.create_task(auto_reply(client, session_name))
        ]
        await asyncio.gather(*tasks)

    except UserDeactivatedBanError:
        print(Fore.RED + f"Account {session_name} is banned. Skipping.")
    except Exception as e:
        print(Fore.RED + f"Unexpected error in session {session_name}: {e}")
    finally:
        await client.disconnect()

# Main logic
async def main():
    display_banner()

    num_sessions = int(input(Fore.MAGENTA + "How many sessions do you want to log in? "))
    active_sessions = []

    for i in range(1, num_sessions + 1):
        session_name = f"session{i}"
        credentials = load_credentials(session_name)

        if credentials:
            print(Fore.GREEN + f"\nUsing saved credentials for session {i}.")
            active_sessions.append((credentials["api_id"], credentials["api_hash"], credentials["phone_number"], session_name))
        else:
            print(Fore.YELLOW + f"\nEnter details for account {i}:")
            api_id = int(input(Fore.CYAN + "Enter API ID: "))
            api_hash = input(Fore.CYAN + "Enter API hash: ")
            phone_number = input(Fore.CYAN + "Enter phone number (with country code): ")

            credentials = {"api_id": api_id, "api_hash": api_hash, "phone_number": phone_number}
            save_credentials(session_name, credentials)
            active_sessions.append((api_id, api_hash, phone_number, session_name))

    tasks = [login_and_execute(api_id, api_hash, phone_number, session_name) for api_id, api_hash, phone_number, session_name in active_sessions]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())