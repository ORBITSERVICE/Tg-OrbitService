import os
import json
import logging
import asyncio
import random
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.messages import ForwardMessagesRequest
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

# Folder to store session credentials
CREDENTIALS_FOLDER = "session_credentials"
if not os.path.exists(CREDENTIALS_FOLDER):
    os.makedirs(CREDENTIALS_FOLDER)

# Fixed auto-reply message
AUTO_REPLY_MESSAGE = """
🌟 *Welcome to OrbitService!* 🌟

📢 Admin Support: @OrbitService  
🛒 Explore Our Store: @OrbitShoppy  
🔍 See Proofs & Reviews: @LegitProofs99  

💬 *Need help or have questions?*  
👉 We’re here to assist you! Feel free to message us anytime.

🚀 *Ready to get started?*  
Check out our store for exclusive deals and services!

Thank you for choosing OrbitService! 😊
"""

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

# Function to auto forward the last saved message to all groups with random delay
async def auto_forward_messages(client, rounds_delay):
    print(Fore.GREEN + "\nAuto Forwarder Started")

    while True:  # Run indefinitely until manually stopped
        # Fetch the last saved message
        saved_messages = await client.get_messages('me', limit=1)  # Get the last saved message
        if not saved_messages:
            print(Fore.RED + "No saved messages found.")
            await asyncio.sleep(60)  # Wait 1 minute before retrying
            continue

        last_message = saved_messages[0]
        print(Fore.CYAN + f"Last saved message: {last_message.text}")

        # Fetch all groups the user has joined
        dialogs = await client.get_dialogs()
        groups = [dialog.entity for dialog in dialogs if dialog.is_group]

        if not groups:
            print(Fore.RED + "No groups found.")
            await asyncio.sleep(60)  # Wait 1 minute before retrying
            continue

        print(Fore.CYAN + f"Forwarding to {len(groups)} groups...")

        # Forward the last saved message to all groups with random delay
        for group in groups:
            try:
                await client(ForwardMessagesRequest(
                    from_peer='me',
                    id=[last_message.id],
                    to_peer=group
                ))
                print(Fore.GREEN + f"Message forwarded to group: {group.title}")
            except Exception as e:
                print(Fore.RED + f"Failed to forward message to group {group.title}: {e}")

            # Add random delay between groups (15 to 30 seconds)
            delay = random.randint(15, 30)
            print(Fore.YELLOW + f"Waiting for {delay} seconds before next group...")
            await asyncio.sleep(delay)

        # Add delay between rounds
        print(Fore.YELLOW + f"Waiting for {rounds_delay} seconds before next round...")
        await asyncio.sleep(rounds_delay)

# Function to auto reply to private messages
async def auto_reply_to_private_messages(client):
    print(Fore.GREEN + "\nAuto Reply to Private Messages Started")

    @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def handler(event):
        try:
            await event.reply(AUTO_REPLY_MESSAGE)
            print(Fore.GREEN + f"Replied to {event.sender_id} with the auto-reply message.")
        except Exception as e:
            print(Fore.RED + f"Failed to reply to {event.sender_id}: {e}")

# Main function
async def main():
    num_sessions = int(input(Fore.CYAN + "Enter the number of sessions: "))
    if num_sessions <= 0:
        print(Fore.RED + "Number of sessions must be greater than 0.")
        return

    # Ask for delay between rounds
    rounds_delay = int(input(Fore.CYAN + "Enter delay between rounds (in seconds): "))

    valid_clients = []

    for i in range(1, num_sessions + 1):
        session_name = f"session{i}"
        credentials = load_credentials(session_name)

        # Check if credentials are valid
        if credentials and "api_id" in credentials and "api_hash" in credentials and "string_session" in credentials:
            api_id = credentials["api_id"]
            api_hash = credentials["api_hash"]
            string_session = credentials["string_session"]
        else:
            # If credentials are missing or invalid, prompt the user
            print(Fore.YELLOW + f"Session {i} credentials are missing or invalid. Please provide the following:")
            api_id = int(input(Fore.CYAN + f"Enter API ID for session {i}: "))
            api_hash = input(Fore.CYAN + f"Enter API Hash for session {i}: ")
            string_session = input(Fore.CYAN + f"Enter string session for session {i}: ")

            # Save the new credentials
            credentials = {
                "api_id": api_id,
                "api_hash": api_hash,
                "string_session": string_session,
            }
            save_credentials(session_name, credentials)

        # Use string session for login
        client = TelegramClient(StringSession(string_session), api_id, api_hash)

        try:
            await client.start()
            print(Fore.GREEN + f"Logged in successfully for session {i}")
            valid_clients.append(client)  # Store client
        except UserDeactivatedBanError:
            print(Fore.RED + f"Session {i} is banned. Skipping...")
            logging.warning(f"Session {i} is banned. Skipping...")
            continue
        except Exception as e:
            print(Fore.RED + f"Failed to login for session {i}: {str(e)}")
            logging.error(f"Failed to login for session {i}: {str(e)}")
            continue

    if not valid_clients:
        print(Fore.RED + "No valid sessions available. Exiting...")
        return

    # Start auto forwarder and auto reply concurrently for all accounts
    tasks = []
    for client in valid_clients:
        tasks.append(auto_forward_messages(client, rounds_delay))
        tasks.append(auto_reply_to_private_messages(client))

    await asyncio.gather(*tasks)

# Run the script
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.RED + "\nScript stopped manually. Exiting...")
