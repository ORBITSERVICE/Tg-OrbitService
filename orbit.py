import os
import time
import random
import hashlib
from getpass import getpass
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import Fore, Style, init

# Initialize colorama for colorful outputs
init(autoreset=True)

# Function to hash a password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Pre-defined hashed password
STORED_PASSWORD_HASH = "b278f73eb9c63685d86077025836fee7077ebc6864e57ca038d103ce2e87aaac"

# Password prompt
entered_password = getpass("Enter the script password: ")
if hash_password(entered_password) != STORED_PASSWORD_HASH:
    print("Incorrect password. Exiting...")
    exit()

# API credentials (fixed, not prompted every time)
api_id = 1234567  # Replace with your actual API ID
api_hash = "your_api_hash"  # Replace with your actual API Hash

# Ask how many sessions to log
num_sessions = int(input("How many sessions do you want to log in? (Enter the number of saved sessions): "))

clients = []

# Handle each session
for i in range(num_sessions):
    session_name = input(f"Enter the name of session {i + 1} (e.g., session1): ")
    client = TelegramClient(session_name, api_id, api_hash)

    try:
        if os.path.exists(f"{session_name}.session"):
            print(f"{Fore.GREEN}Using saved session for {session_name}")
            client.start()
            clients.append(client)
        else:
            print(f"{Fore.RED}Session file {session_name}.session not found. Skipping this session.")
    except Exception as e:
        print(f"{Fore.RED}Failed to start session for {session_name}: {e}")

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
            print(f"{Fore.CYAN}Last saved message retrieved. Forwarding...")
        else:
            print(f"{Fore.RED}No messages found in Saved Messages.")
            return
    except Exception as e:
        print(f"{Fore.RED}Failed to retrieve the last saved message: {e}")
        return

    # Forward the last saved message to all groups
    groups = [d for d in await client.get_dialogs() if d.is_group]
    for group in groups:
        try:
            await client.forward_messages(group.id, last_saved_message.id, "me")
            print(f"{Fore.GREEN}Message forwarded to group: {group.name or group.id}")
        except Exception as e:
            print(f"{Fore.RED}Could not forward message to {group.name or group.id}: {e}")

        # Add delay between groups
        print(f"{Fore.CYAN}Waiting {delay_between_groups} seconds before the next group...")
        time.sleep(delay_between_groups)

    # Delay after completing all groups
    print(f"{Fore.CYAN}Waiting {delay_after_all_groups} seconds before the next cycle...")
    time.sleep(delay_after_all_groups)

# Function to handle Pro Leaver
async def pro_leaver(client):
    groups = [d for d in await client.get_dialogs() if d.is_group]
    for group in groups:
        try:
            await client.send_message(group.id, "Test message")
            print(f"{Fore.YELLOW}Test message sent to group: {group.name or group.id}")
        except Exception as e:
            print(f"{Fore.RED}Could not send test message to {group.name or group.id}: {e}")
            try:
                await client.delete_dialog(group.id)
                print(f"{Fore.BLUE}Left group: {group.name or group.id}")
            except Exception as leave_error:
                print(f"{Fore.RED}Failed to leave group {group.name or group.id}: {leave_error}")

# Main Function
async def main():
    for client in clients:
        print(f"\n{Fore.CYAN}Choose an option for session {client.session.filename.split('/')[-1]}:")
        print(f"{Fore.GREEN}1] Auto Forward {Style.RESET_ALL}- Forward messages to all groups with delay.")
        print(f"{Fore.MAGENTA}2] Pro Leaver {Style.RESET_ALL}- Leave groups where test message can't be sent.")

        option = input("\nEnter your choice (1 or 2): ")
        if option == "1":
            delay_after_all_groups = float(input("Enter the delay (in seconds) after completing all groups: "))
            delay_between_groups = 3  # Fixed delay of 3 seconds between groups
            print(f"{Fore.GREEN}Starting Auto Forward...")
            await auto_forward(client, delay_after_all_groups, delay_between_groups)
        elif option == "2":
            print(f"{Fore.MAGENTA}Starting Pro Leaver...")
            await pro_leaver(client)
        else:
            print(f"{Fore.RED}Invalid option. Skipping session...")

# Run the script
for client in clients:
    with client:
        client.loop.run_until_complete(main())