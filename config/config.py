import os
from pathlib import Path
from dotenv import load_dotenv

# Calculate base directory (absolute path to edu_master_bot)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")

class Config:
    BASE_DIR = BASE_DIR
    BOT_TOKEN = os.getenv("BOT_TOKEN", "8234813786:AAG3tV0mlQdj8S2gWnF4RVp9zuieTHCwdY8")

    ADMIN_ID = int(os.getenv("ADMIN_ID", "8420258761"))
    CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@boliqulov700")

    # Folders for storage
    PDF_DIR = BASE_DIR / "storage" / "pdfs"
    CERTIFICATE_DIR = BASE_DIR / "storage" / "certificates"

    @classmethod
    def ensure_dirs(cls):
        cls.PDF_DIR.mkdir(parents=True, exist_ok=True)
        cls.CERTIFICATE_DIR.mkdir(parents=True, exist_ok=True)

# Ensure folders exist
Config.ensure_dirs()
