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
    os.makedirs(CREDENTIALS_FOLDER)

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

async def setup_auto_reply(client, session_name):
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private and not event.out:
            try:
                await event.respond(AUTO_REPLY_MESSAGE)
                logging.info(f"Replied to {event.sender_id} in {session_name}")
                print(Fore.GREEN + f"[{session_name}] Replied to {event.sender_id}")
            except errors.FloodWaitError as e:
                print(Fore.YELLOW + f"[{session_name}] Flood wait for {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                logging.error(f"[{session_name}] Auto-Reply Error: {str(e)}")
                print(Fore.RED + f"[{session_name}] Auto-Reply Error: {str(e)}")

async def send_message_copy(client, last_message, session_name, group, delay):
    try:
        await asyncio.sleep(delay)
        message_text = last_message.message
        await client.send_message(group, message_text, link_preview=False)
        print(Fore.CYAN + f"[{session_name}] Message copied to {group.title}")
    except errors.FloodWaitError as e:
        print(Fore.YELLOW + f"[{session_name}] Flood wait for {e.seconds} seconds")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logging.error(f"[{session_name}] Send Error: {str(e)}")
        print(Fore.RED + f"[{session_name}] Send Error: {str(e)}")

async def initialize_session(session_name, credentials):
    try:
        client = TelegramClient(
            StringSession(credentials['session_string']),
            credentials['api_id'],
            credentials['api_hash']
        )
        
        await client.connect()
        if not await client.is_user_authorized():
            print(Fore.RED + f"[{session_name}] Authorization failed")
            return None, None

        # Setup auto-reply first
        await setup_auto_reply(client, session_name)

        # Get last saved message
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
            print(Fore.YELLOW + f"[{session_name}] No saved messages found")
            return client, None

        last_message = history.messages[0]
        return client, last_message

    except UserDeactivatedBanError:
        print(Fore.RED + f"[{session_name}] Account banned")
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Init Error: {str(e)}")

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
            if client:
                active_clients.append((client, last_message, session_name))
        
        if not active_clients:
            print(Fore.RED + "No active sessions available. Exiting.")
            return
        
        print(Fore.GREEN + f"\n{len(active_clients)} sessions initialized. Starting operations...")
        
        # Start all clients
        for client, _, session_name in active_clients:
            try:
                await client.start()
                print(Fore.GREEN + f"[{session_name}] Client started successfully")
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Start failed: {str(e)}")
                active_clients.remove((client, _, session_name))
        
        # Main operations loop
        while True:
            for index, (client, last_message, session_name) in enumerate(active_clients):
                if not last_message:
                    continue
                
                try:
                    async for dialog in client.iter_dialogs():
                        if dialog.is_group:
                            await send_message_copy(
                                client,
                                last_message,
                                session_name,
                                dialog.entity,
                                action_delay if index > 0 else 0
                            )
                except Exception as e:
                    print(Fore.RED + f"[{session_name}] Dialog Error: {str(e)}")
            
            await asyncio.sleep(60)  # Wait 1 minute between cycles

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nStopped by User")
    except ValueError:
        print(Fore.RED + "Invalid Number Input")
    finally:
        # Disconnect all clients
        for client, _, session_name in active_clients:
            try:
                await client.disconnect()
                print(Fore.YELLOW + f"[{session_name}] Disconnected")
            except:
                pass

if __name__ == "__main__":
    asyncio.run(main())
