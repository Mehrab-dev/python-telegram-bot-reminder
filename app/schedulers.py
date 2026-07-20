from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from sqlalchemy import or_

from app.database.database import LocalSession
from app.database.models import TaskModel, TaskStatus
from app.bot.client import bot


scheduler = BackgroundScheduler()


# def completed_task():

#     now = datetime.now()
#     target = now + timedelta(hours=2)
#     start = target - timedelta(seconds=10)
#     end = target + timedelta(seconds=10)

#     db = LocalSession()
#     task = db.query(TaskModel).filter(
#         TaskModel.status==TaskStatus.PENDING),
#         TaskModel.due_date.between(start, end).all()

#     for item in task:
#         user_id = item.user_id

#         response = f"""
#                     ⏰ تا پایان زمان انجام وظیفه شما 2 ساعت بیشتر نمونده
#                     🔹 نام وظیفه : {item.title}
#                     📂 توضیحات وظیفه : {item.description}
#                 """
#         bot.send_message(
#             chat_id=user_id,
#             text=response
#         )

#         item.status = TaskStatus.COMPLETED

#     db.commit()
#     db.close()

# scheduler.add_job(
#     completed_task,
#     "interval",
#     seconds=10
# )


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

    for task in tasks:
        user_id = task.user_id
        response = f"""
                    🔔 یادآوری \n
                    سلام 👋
                    فقط 2 ساعت تا انجام وظیفه زیر زمان داری :\n
                    📌 عنوان وظیفه : {task.title}
                    📝 توضیحان وظیفه : {task.description or "❌ ندارد"} 
                    🕜 زمان انجام : {task.due_date} \n
                    🌱 موفق باشی
                """
        try:
            bot.send_message(
                chat_id=user_id,
                text=response
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
        response = f"""
                🌙 یادآوری \n
                این پیام جهت یادآوری وظیفه ثبت شده شما ارسال شده است.\n
                📌 عنوان وظیفه : {task.title}
                📝 توضیحات وظیفه : {task.description}
                🕜 زمان انجام : {task.due_date} \n
                🌱 موفق باشی
            """
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