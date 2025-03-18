from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("Telethon String Session Generator")

# Ask for API ID and API Hash
API_ID = input("Enter your API ID (from https://my.telegram.org): ")
API_HASH = input("Enter your API Hash (from https://my.telegram.org): ")

# Ask for phone number
PHONE_NUMBER = input("Enter your phone number (with country code, e.g., +1234567890): ")

# Create a Telethon client
with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    # Connect and log in
    client.connect()

    if not client.is_user_authorized():
        # Send OTP if not logged in
        try:
            client.send_code_request(PHONE_NUMBER)
            code = input("Enter the OTP you received: ")
            client.sign_in(PHONE_NUMBER, code)
        except Exception as e:
            print(f"Error during login: {e}")
            if "password" in str(e):  # Handle 2FA
                password = input("Your account has 2FA enabled. Enter your 2FA password: ")
                client.sign_in(password=password)

    # Get the string session
    string_session = client.session.save()

    # Display the string session
    print("\nYour Telethon string session is:")
    print(string_session)
    print("\nSave this string session in a safe place!")