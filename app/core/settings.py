from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Setting(BaseSettings):
    API_KEY: str = ""
    SQLALCHEMY_DATABASE_URL: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_SECRET_ID: str = ""
    REDIRECT_URI: str = ""


setting = Setting()