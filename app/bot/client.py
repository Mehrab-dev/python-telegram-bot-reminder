import telebot
from telebot import apihelper

from app.core.settings import setting

apihelper.API_URL = "https://tapi.bale.ai/bot{0}/{1}"
API_KEY = setting.API_KEY

bot = telebot.TeleBot(API_KEY)
