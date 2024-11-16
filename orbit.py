import os
import time
import random
import json
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import Fore, Style, init
import pyfiglet

# Initialize colorama for colorful outputs
init(autoreset=True)

# Folder for saving session credentials
CREDENTIALS_FOLDER = "sessions"

# Create the sessions folder if it doesn't exist
if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

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

# Function to display banner with full color
def display_banner():
    banner = pyfiglet.figlet_format("OrbitService")
    print(Fore.RED + banner)
    print(Fore.GREEN + Style.BRIGHT + "Made by @OrbitService\n")

# Function to forward the last saved message
async def auto_forward(client, delay_after_all_groups, delay_between_groups):
    # Retrieve the last message from "Saved Messages"
    try:
        history = await client(GetHistoryRequest(
            peer="me",  # 'me' represents the "Saved Messages" chat
            limit=1,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0
        ))
        if history.messages:
            last_saved_message = history.messages[0]
            print(Fore.CYAN + "Last saved message retrieved. Forwarding...\n")
        else:
            print(Fore.RED + "No messages found in Saved Messages.")
            return
    except Exception as e:
        print(Fore.RED + f"Failed to retrieve the last saved message: {e}")
        return

    # Forward the last saved message to all groups
    groups = [d for d in await client.get_dialogs() if d.is_group]
    for group in groups:
        try:
            await client.forward_messages(group.id, last_saved_message.id, "me")
            print(Fore.GREEN + f"Message forwarded to group: {group.name or group.id}")
        except Exception as e:
            print(Fore.RED + f"Could not forward message to {group.name or group.id}: {e}")

        # Delay between groups
        print(Fore.YELLOW + f"Waiting {delay_between_groups} seconds before the next group...")
        time.sleep(delay_between_groups)

    # Delay after completing all groups
    print(Fore.YELLOW + f"Waiting {delay_after_all_groups} seconds before the next cycle...")
    time.sleep(delay_after_all_groups)

# Main logic
async def main():
    display_banner()  # Display the OrbitService banner

    num_sessions = int(input(Fore.MAGENTA + "How many sessions would you like to log in? "))  # Ask for the number of sessions
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
            phone_number = input(Fore.CYAN + f"Enter phone number for session {i} (with country code): ")

            credentials = {
                "api_id": api_id,
                "api_hash": api_hash,
                "phone_number": phone_number,
            }
            save_credentials(session_name, credentials)

        client = TelegramClient(session_name, api_id, api_hash)
        await client.start(phone=phone_number)
        clients.append(client)

    for client in clients:
        delay_after_all_groups = float(input(Fore.MAGENTA + "Enter delay (in seconds) after completing all groups: "))
        delay_between_groups = 3  # Fixed delay of 3 seconds between groups
        print(Fore.GREEN + "Starting Auto Forward...")
        await auto_forward(client, delay_after_all_groups, delay_between_groups)

    # Disconnect all clients
    for client in clients:
        await client.disconnect()

# Entry point
if __name__ == "__main__":
    asyncio.run(main())