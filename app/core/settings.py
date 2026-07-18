from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Setting(BaseSettings):
    API_KEY: str = ""
    SQLALCHEMY_DATABASE_URL: str = ""


setting = Setting()