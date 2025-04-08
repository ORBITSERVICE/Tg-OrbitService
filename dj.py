import asyncio
import os
import json
import logging
from telethon import TelegramClient, events, errors
from telethon.errors import UserDeactivatedBanError
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.sessions import StringSession
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

AUTO_REPLY_MESSAGE = "Msg To @OrbitService"

def save_credentials(session_name, api_id, api_hash, session_string):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, 'w') as f:
        json.dump({
            'api_id': api_id,
            'api_hash': api_hash,
            'session_string': session_string
        }, f)

def load_credentials(session_name):
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

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
                print(Fore.GREEN + f"Replied to {event.sender_id} in {session_name}")
            except errors.FloodWaitError as e:
                print(Fore.YELLOW + f"Flood wait for {e.seconds} seconds in {session_name}")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logging.error(f"Auto-Reply Error in {session_name}: {str(e)}")
                print(Fore.RED + f"Error in {session_name}: {str(e)}")

async def forward_with_delay(client, last_message, session_name, group, delay):
    try:
        await asyncio.sleep(delay)
        await client.send_message(group, last_message.message, link_preview=False)
        print(Fore.GREEN + f"Message forwarded to {group.title} from {session_name}")
    except errors.FloodWaitError as e:
        print(Fore.YELLOW + f"Flood wait for {e.seconds} seconds when forwarding from {session_name}")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logging.error(f"Forward Error in {session_name}: {str(e)}")
        print(Fore.RED + f"Forward Error in {session_name}: {str(e)}")

async def initialize_session(session_name, credentials):
    try:
        client = TelegramClient(
            StringSession(credentials['session_string']),
            credentials['api_id'],
            credentials['api_hash']
        )
        await client.connect()

        if not await client.is_user_authorized():
            print(Fore.RED + f"Session authorization failed for {session_name}")
            return None, None

        saved_peer = await client.get_input_entity('me')
        history = await client(GetHistoryRequest(
            peer=saved_peer,
            limit=1,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            max_id=0,
            min_id=0,
            hash=0
        ))

        if not history.messages:
            print(Fore.RED + f"No messages in Saved Messages for {session_name}")
            return None, None

        last_message = history.messages[0]
        client.add_event_handler(auto_reply(client, session_name))
        return client, last_message

    except UserDeactivatedBanError:
        print(Fore.RED + f"Session {session_name} is BANNED!")
    except Exception as e:
        print(Fore.RED + f"Error initializing {session_name}: {str(e)}")

    return None, None

async def main():
    display_banner()

    try:
        num_sessions = int(input("Enter Number of Sessions: "))
        action_delay = int(input("Delay between Actions (Seconds): "))
        
        active_clients = []
        
        # Initialize all sessions
        for i in range(1, num_sessions + 1):
            session_name = f'session{i}'
            credentials = load_credentials(session_name)
            
            if not credentials:
                print(Fore.CYAN + f"\nSetting up new session: {session_name}")
                api_id = int(input("API ID: "))
                api_hash = input("API Hash: ")
                session_string = input("Session String: ")
                save_credentials(session_name, api_id, api_hash, session_string)
                credentials = {
                    'api_id': api_id,
                    'api_hash': api_hash,
                    'session_string': session_string
                }
            else:
                print(Fore.GREEN + f"Using saved session: {session_name}")
            
            client, last_message = await initialize_session(session_name, credentials)
            if client and last_message:
                active_clients.append((client, last_message, session_name))
        
        if not active_clients:
            print(Fore.RED + "No active sessions available. Exiting.")
            return
        
        print(Fore.GREEN + f"\n{len(active_clients)} sessions initialized. Starting operations...")
        
        # Start all clients
        for client, _, _ in active_clients:
            await client.start()
        
        # Main loop for forwarding messages
        while True:
            for index, (client, last_message, session_name) in enumerate(active_clients):
                try:
                    async for dialog in client.iter_dialogs():
                        if dialog.is_group:
                            await forward_with_delay(
                                client,
                                last_message,
                                session_name,
                                dialog.entity,
                                action_delay if index > 0 else 0
                            )
                except Exception as e:
                    print(Fore.RED + f"Error in {session_name} main loop: {str(e)}")
            
            await asyncio.sleep(10)  # Small delay between full cycles

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nStopped by User")
    except ValueError:
        print(Fore.RED + "Invalid Number Input")
    finally:
        # Disconnect all clients
        for client, _, _ in active_clients:
            try:
                await client.disconnect()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())
