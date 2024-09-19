import os
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    DEBUG = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    SECRET_KEY = os.getenv("SECRET_KEY", "horiar-bir-web3-platformu")
    RUNPOD_URL = os.getenv("RUNPOD_URL")
    RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
    OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")

