import os
from dotenv import load_dotenv

load_dotenv()

class DevelopmentConfig:
    DEBUG = True
    SECRET_KEY = os.getenv("SECRET_KEY")
    MONGO_URI_PRIMARY = os.getenv("MONGO_URI_PRIMARY")
    MONGO_URI_SECONDARY = os.getenv("MONGO_URI_SECONDARY")
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    SECRET_KEY = os.getenv("SECRET_KEY", "horiar-bir-web3-platformu")
    RUNPOD_URL = os.getenv("RUNPOD_URL")
    RUNPOD_UPSCALE_URL = os.getenv("RUNPOD_UPSCALE_URL")
    RUNPOD_VIDEO_URL_COG = os.getenv("RUNPOD_VIDEO_URL_COG")
    RUNPOD_VIDEO_URL_HUNYUAN = os.getenv("RUNPOD_VIDEO_URL_HUNYUAN")
    RUNPOD_I2I_URL = os.getenv('RUNPOD_I2I_URL')
    RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
    OPEN_AI_KEY = os.getenv("OPEN_AI_KEY")
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    MAIL_DEBUG = os.getenv('MAIL_DEBUG')
    SMTP_DEBUG_LEVEL = os.getenv('SMTP_DEBUG_LEVEL')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    S3_FOLDER_UPSCALE_IMAGE = os.getenv('S3_FOLDER_UPSCALE_IMAGE')
    S3_FOLDER_WEBP_IMAGE = os.getenv('S3_FOLDER_WEBP_IMAGE')
    S3_FOLDER_VIDEO = os.getenv('S3_FOLDER_VIDEO')
    S3_FOLDER_I2I_IMAGE = os.getenv('S3_FOLDER_I2I_IMAGE')
    S3_FOLDER_ANNOUNCEMENT = os.getenv('S3_FOLDER_ANNOUNCEMENT')
    MERCHANT_ID = os.getenv('MERCHANT_ID')
    MERCHANT_KEY = os.getenv('MERCHANT_KEY')
    MERCHANT_SALT = os.getenv('MERCHANT_SALT')
    MERCHANT_OK_URL = os.getenv('MERCHANT_OK_URL')
    MERCHANT_FAIL_URL = os.getenv('MERCHANT_FAIL_URL')
    ENTERPRISE_ENCRYPTION_KEY = os.environ.get('ENTERPRISE_ENCRYPTION_KEY')


