import os
from dotenv import load_dotenv

def check_env():
    load_dotenv()
    print(f"LINE_CHANNEL_ACCESS_TOKEN exists: {bool(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))}")
    print(f"LINE_CHANNEL_SECRET exists: {bool(os.getenv('LINE_CHANNEL_SECRET'))}")
    print(f"GOOGLE_GEMINI_API_KEY exists: {bool(os.getenv('GOOGLE_GEMINI_API_KEY'))}")

if __name__ == '__main__':
    check_env()
