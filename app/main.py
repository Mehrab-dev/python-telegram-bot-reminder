from fastapi import FastAPI, Query
import uvicorn
import threading
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.bot.client import bot
import app.bot.handler
from app.database.database import Base, engine, LocalSession
from app.database.models import UserModel
from app.oauth_handler import GoogleOAuthHandler
from app.schedulers import scheduler_start

Base.metadata.create_all(bind=engine)

fastapi_app = FastAPI()


@fastapi_app.get("/")
def root():
    return {"message": "FastAPI is running!"}


@fastapi_app.get("/oauth2callback")
def oauth2callback(code: str = Query(...), state: str = Query(...)):
    
    try:
        user_id = int(state)
        
        oauth = GoogleOAuthHandler()
        tokens = oauth.exchange_code_for_tokens(code)
        
        db = LocalSession()
        user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
        
        if user:
            user.access_token = tokens['access_token']
            user.refresh_token = tokens['refresh_token']
            user.token_expiry = datetime.now() + timedelta(seconds=tokens['expires_in'])
        else:
            user = UserModel(
                user_id=user_id,
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                token_expiry=datetime.now() + timedelta(seconds=tokens['expires_in'])
            )
            db.add(user)

        # بعد از db.commit() و قبل از db.close()
        # اگر کاربر calendar_id نداشت، یه تقویم جدید بساز
        if not user.calendar_id:
            try:
                from app.calendar_handler import CalendarHandler
                calendar_handler = CalendarHandler(
                    access_token=user.access_token,
                    refresh_token=user.refresh_token
                )
                new_calendar_id = calendar_handler.create_calendar("Telegram Reminder")
                user.calendar_id = new_calendar_id
                db.commit()
                print(f"✅ تقویم جدید ساخته شد: {new_calendar_id}")
            except Exception as e:
                print(f"❌ خطا در ساخت تقویم: {e}")
        db.commit()
        db.close()
        

        try:

            keyboard = InlineKeyboardMarkup()
            back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
            keyboard.add(back_home_btn)

            bot.send_message(
                chat_id=user_id,
                text="✅ اتصال شما به Google Calendar با موفقیت انجام شد!",
                reply_markup=keyboard
            )
            print("📨 پیام موفقیت به کاربر ارسال شد")
        except Exception as e:
            print(f"❌ خطا در ارسال پیام: {e}")
        
        return """
        <h2>✅ اتصال با موفقیت انجام شد!</h2>
        <p>به ربات برگرد و /start بزن.</p>
        """
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        import traceback
        traceback.print_exc()
        return f"<h2>❌ خطا: {str(e)}</h2>", 500


def run_fastapi():
    uvicorn.run(fastapi_app, host="127.0.0.1", port=8081)

def start_bot():
    print("🤖 ربات شروع به کار کرد...")
    scheduler_start()
    bot.infinity_polling()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 برنامه در حال اجرا...")
    print("=" * 50)
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()
    start_bot()