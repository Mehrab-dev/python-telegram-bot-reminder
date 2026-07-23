import telebot
from telebot import apihelper

from app.core.settings import setting

API_KEY = setting.API_KEY

bot = telebot.TeleBot(API_KEY)
