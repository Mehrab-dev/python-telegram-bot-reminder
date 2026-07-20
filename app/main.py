from app.bot.client import bot
import app.bot.handler
from app.database.database import Base, engine
from app.schedulers import scheduler_start

Base.metadata.create_all(bind=engine)
scheduler_start()
bot.infinity_polling()