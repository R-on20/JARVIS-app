import os

from dotenv import load_dotenv

load_dotenv()


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

CREDENTIALS_DIR = os.path.join(BASE_DIR, "credentials")

GOOGLE_CREDENTIALS_FILE = os.path.join(
    CREDENTIALS_DIR,
    "credentials.json"
)

GOOGLE_TOKEN_FILE = os.path.join(
    CREDENTIALS_DIR,
    "token.json"
)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]