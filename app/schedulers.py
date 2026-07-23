from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy import or_
import jdatetime

from app.database.database import LocalSession
from app.database.models import TaskModel, TaskStatus
from app.bot.client import bot


scheduler = BackgroundScheduler()

def convert_to_jalali(date_time):
    jalali_date = jdatetime.datetime.fromgregorian(datetime=date_time)
    return {
        'date': jalali_date.strftime("%Y/%m/%d"),
        'time': jalali_date.strftime("%H:%M")
    }



def send_final_notification():

    now = datetime.now()
    target = now + timedelta(hours=2)
    start = target
    end = target + timedelta(seconds=10)

    db = LocalSession()
    tasks = db.query(TaskModel).filter(
        TaskModel.status == TaskStatus.PENDING, 
        TaskModel.due_date.between(start, end)
    ).all()

    keyboard = InlineKeyboardMarkup()
    back_home_btn = InlineKeyboardButton(text="متوجه شدم", callback_data="back_home")
    keyboard.add(back_home_btn)

    for task in tasks:
        user_id = task.user_id
        jalali = convert_to_jalali(task.due_date)                
        response = (
                f"🔔 یادآوری \n"
                f"👋 سلام خواستم بهت یادآوری کنم تا وظیفه زیر 2 ساعت بیشتر نمونده : \n"
                f"📌 عنوان: {task.title}\n"
                f"📝 توضیحات: {task.description or '❌ ندارد'}\n"
                f"📆 تاریخ: {jalali['date']}\n"
                f"🕐 ساعت: {jalali['time']}\n\n"
                "🌱 موفق باشی"
            )
        try:
            bot.send_message(
                chat_id=user_id,
                text=response,
                reply_markup=keyboard
            )
            task.status = TaskStatus.COMPLETED
        
        except Exception:
            continue

    db.commit()
    db.close()



def send_notification():

    now = datetime.now()
    limit_date = now + timedelta(hours=12)

    db = LocalSession()
    tasks = db.query(TaskModel).filter(
        TaskModel.status == TaskStatus.PENDING,
        TaskModel.due_date > limit_date
    ).all()

    for task in tasks:
        user_id = task.user_id
        jalali = convert_to_jalali(task.due_date)
                
        response = (
            f"🔔 یادآوری \n"
            f"📌 عنوان: {task.title}\n"
            f"📝 توضیحات: {task.description or '❌ ندارد'}\n"
            f"📆 تاریخ: {jalali['date']}\n"
            f"🕐 ساعت: {jalali['time']}\n\n"
            "🌱 موفق باشی"
        )
        
        try:
            bot.send_message(
                chat_id=user_id,
                text=response
            )
        except Exception:
            continue
    
    db.close()



scheduler.add_job(
    send_final_notification,
    "interval",
    seconds=10
)


scheduler.add_job(
    send_notification,
    "cron",
    hour=22,
    minute=00
)


def scheduler_start():
    scheduler.start()    