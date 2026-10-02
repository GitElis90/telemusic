"""
Run this ONCE on your own computer (not on the server) to log into your
Telegram account and generate a session string.

1. Go to https://my.telegram.org -> "API development tools" -> create an app.
   Copy the "api_id" (a number) and "api_hash" (a long string).
2. pip install telethon
3. Run:  python generate_session.py
4. Enter your api_id, api_hash, phone number, and the login code Telegram
   sends you (and your 2FA password if you have one set).
5. Copy the printed SESSION_STRING somewhere safe. You'll paste it into
   Render as an environment variable. Never share it publicly -- it is
   equivalent to being logged into your Telegram account.
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

def main():
    api_id = int(input("api_id: ").strip())
    api_hash = input("api_hash: ").strip()

    with TelegramClient(StringSession(), api_id, api_hash) as client:
        session_string = client.session.save()
        print("\n=== SAVE THIS SOMEWHERE SAFE ===")
        print("SESSION_STRING=" + session_string)
        print("=================================\n")
        print("You can now close this. Use the value above as the")
        print("SESSION_STRING environment variable on Render.")

if __name__ == "__main__":
    main()
