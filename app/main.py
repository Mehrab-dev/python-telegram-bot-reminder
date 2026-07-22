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


Base.metadata.create_all(bind=engine)

fastapi_app = FastAPI()


@fastapi_app.get("/")
def root():
    return {"message": "FastAPI is running!"}


@fastapi_app.get("/oauth2callback")
def oauth2callback(code: str = Query(...), state: str = Query(...)):
    print("=" * 50)
    print("📥 درخواست به oauth2callback رسید!")
    print(f"📝 Code: {code[:20]}...")
    print(f"👤 State: {state}")
    print("=" * 50)
    
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

def run_bot():
    print("🤖 ربات شروع به کار کرد...")
    bot.infinity_polling()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 برنامه در حال اجرا...")
    print("=" * 50)
    fastapi_thread = threading.Thread(target=run_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()
    run_bot()