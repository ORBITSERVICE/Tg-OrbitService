import os
import json
import asyncio
import random
from telethon import TelegramClient, errors
from telethon.tl.types import InputPeerUser
from telethon.tl.functions.channels import InviteToChannelRequest

# Directory for storing session files
CREDENTIALS_FOLDER = 'sessions'

if not os.path.exists(CREDENTIALS_FOLDER):
    os.mkdir(CREDENTIALS_FOLDER)

# Save credentials
def save_credentials(session_name, credentials):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, 'w') as f:
        json.dump(credentials, f)

# Load credentials
def load_credentials(session_name):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

# Log in and fetch groups
async def login_and_fetch_groups(session_name, api_id, api_hash, phone):
    client = TelegramClient(session_name, api_id, api_hash)
    await client.start(phone=phone)

    if not await client.is_user_authorized():
        print(f"Session {session_name} is not authorized.")
        return None, []

    groups = [dialog for dialog in await client.get_dialogs() if dialog.is_group]
    return client, groups

# Add members to target group
async def add_members(clients, selections, delay_range):
    while selections:
        for client, (source_group, target_group) in selections.items():
            if not source_group or not target_group:
                continue

            try:
                print(f"Fetching members from {source_group.title}...")
                members = await client.get_participants(source_group)
                target_members = [user.id for user in await client.get_participants(target_group)]

                for member in members:
                    if member.bot or member.deleted or member.id in target_members:
                        continue

                    try:
                        user = InputPeerUser(member.id, member.access_hash)
                        await client(InviteToChannelRequest(target_group, [user]))
                        print(f"Added {member.username or member.id} to {target_group.title}.")
                    except errors.FloodWaitError as e:
                        print(f"Flood wait error. Sleeping for {e.seconds} seconds.")
                        await asyncio.sleep(e.seconds)
                        continue
                    except Exception as e:
                        print(f"Failed to add {member.username or member.id}: {e}")
                        continue

                    delay = random.randint(*delay_range)
                    print(f"Waiting for {delay} seconds...")
                    await asyncio.sleep(delay)

            except Exception as e:
                print(f"Error in adding members with {client.session.filename}: {e}")

        print("All accounts have processed their tasks. Waiting for next round...")

# Main function
async def main():
    num_sessions = int(input("How many sessions do you want to log in? "))
    delay_range = (
        int(input("Enter minimum delay between adds (in seconds): ")),
        int(input("Enter maximum delay between adds (in seconds): "))
    )

    clients = {}
    selections = {}

    # Log in to specified number of accounts
    for i in range(1, num_sessions + 1):
        session_name = f'session{i}'
        credentials = load_credentials(session_name)

        if credentials:
            print(f"Using saved credentials for {session_name}.")
        else:
            api_id = int(input(f"Enter API ID for session {i}: "))
            api_hash = input(f"Enter API Hash for session {i}: ")
            phone = input(f"Enter phone number for session {i}: ")
            credentials = {'api_id': api_id, 'api_hash': api_hash, 'phone': phone}
            save_credentials(session_name, credentials)

        try:
            client, groups = await login_and_fetch_groups(session_name, credentials['api_id'], credentials['api_hash'], credentials['phone'])
            if client:
                clients[client] = groups
        except Exception as e:
            print(f"Failed to log in session {session_name}: {e}")

    # Select source and target groups for each account
    for client, groups in clients.items():
        print("\nAvailable groups:")
        for idx, group in enumerate(groups, start=1):
            print(f"{idx}. {group.title}")

        source_idx = int(input("Select the source group (number): ")) - 1
        target_idx = int(input("Select the target group (number): ")) - 1
        selections[client] = (groups[source_idx], groups[target_idx])

    # Start the member-adding process
    await add_members(clients, selections, delay_range)

    # Disconnect all clients
    for client in clients:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
