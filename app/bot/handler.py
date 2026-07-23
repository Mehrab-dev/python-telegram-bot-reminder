from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timezone, timedelta
from app.oauth_handler import GoogleOAuthHandler
import jdatetime
import threading

from app.bot.client import bot
from app.bot.keyboards import (start_keyboard, add_title_task_keyboard, add_des_task_keyboard, add_due_date_task_keyboard, task_detail_keyboard)
from app.database.database import LocalSession
from app.database.models import TaskModel, TaskStatus, UserModel
from app.api.parsers.date_parser import parse_date
from app.api.parsers.task_parser import parse_task
from app.api.utils.calculate_task import calculate_task


user_state = {}
user_temp_task = {}
user_history = {}
state_lock = threading.Lock()


def convert_to_jalali(date_time):
    jalali_date = jdatetime.datetime.fromgregorian(datetime=date_time)
    return {
        'date': jalali_date.strftime("%Y/%m/%d"),
        'time': jalali_date.strftime("%H:%M")
    }



@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id
    with state_lock:
        if user_id not in user_history:
            user_history[user_id] = []
        user_state[user_id] = "main_menu"
        first_name = message.chat.first_name

        bot.send_message(
            chat_id=message.chat.id,
            text=f"سلام {first_name} عزیز 👋\n" \
            "لطفا یکی از گزینه های زیر را انتخاب کن",
            reply_markup=start_keyboard()
        )



# handler for add task
@bot.callback_query_handler(func=lambda call: call.data == "add_task")
def add_task_handler(call):
    user_id = call.from_user.id

    with state_lock:
        if user_id not in user_state:
            user_state[user_id] = "main_menu"

        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

        user_state[user_id] = "waiting_title"
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🔹 نام وظیفه خود را وارد کنید :",
            reply_markup=add_title_task_keyboard()
        )




@bot.callback_query_handler(func=lambda call: call.data == "google_login")
async def google_login_handler(call):
    user_id = call.from_user.id
    
    db = LocalSession()
    user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
    db.close()

    keyboard = InlineKeyboardMarkup()
    btn_back = InlineKeyboardButton("🔙 برگشت به منو", callback_data="back_home")
    keyboard.add(btn_back)

    if user and user.access_token:
        bot.answer_callback_query(
            call.id, 
            "✅ شما قبلاً به Google Calendar متصل شده‌اید!", 
            show_alert=True
        )
        return
    
    oauth = GoogleOAuthHandler()
    auth_link = oauth.get_auth_link(user_id)
    
    keyboard = InlineKeyboardMarkup()
    btn_google = InlineKeyboardButton("🔗 رفتن به صفحه لاگین گوگل", url=auth_link)
    btn_back = InlineKeyboardButton("🏠 بازگشت یه صفحه اصلی", callback_data="back_home")
    keyboard.add(btn_google)
    keyboard.add(btn_back)

    auth_link = oauth.get_auth_link(user_id)
    print(f"🔗 لینک ارسالی به کاربر: {auth_link}")
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🔐 برای اتصال به Google Calendar، روی دکمه زیر کلیک کن:\n\n"
             "✅ بعد از لاگین، دوباره /start رو بزن تا وارد ربات بشی.",
        reply_markup=keyboard
    )



# handler for logout from google calendar
@bot.callback_query_handler(func=lambda call: call.data == "logout")
def logout_handler(call):
    user_id = call.from_user.id
    first_name = call.message.chat.first_name
    
    db = LocalSession()
    user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
    
    if not user or not user.access_token:
        db.close()
        bot.answer_callback_query(
            call.id, 
            "❌ شما در حال حاضر لاگین نیستید!", 
            show_alert=True
        )
        return
    
    user.access_token = ""
    user.refresh_token = ""
    user.token_expiry = datetime.now() - timedelta(days=1)
    db.commit()
    db.close()
    
    bot.answer_callback_query(
        call.id, 
        "✅ از حساب گوگل خارج شدید!", 
        show_alert=True
    )
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"سلام {first_name} عزیز 👋\nلطفا یکی از گزینه های زیر را انتخاب کن",
        reply_markup=start_keyboard()
    )



# handler for list task
@bot.callback_query_handler(func=lambda call: call.data == "list_task")
def list_task_handler(call):
    user_id = call.from_user.id
    with state_lock:
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

        user_state[user_id] = "waiting_task_list"

    db = LocalSession()
    tasks = db.query(TaskModel).filter_by(user_id=user_id, status=TaskStatus.PENDING).order_by(TaskModel.id.desc()).all()
    keyboard = InlineKeyboardMarkup()
    for item in tasks:
        task_button = InlineKeyboardButton(
            text=item.title,
            callback_data=f"task_{item.id}"
        )
        keyboard.add(task_button)
    
    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")
    keyboard.add(back_btn)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📋 لیست وظایف :",
        reply_markup=keyboard
    )


# list completed tasks
@bot.callback_query_handler(func=lambda call: call.data == "comp_list")
def list_completed_task_handler(call):
    db = LocalSession()
    tasks = db.query(TaskModel).filter(
        TaskModel.status == TaskStatus.COMPLETED
    ).all()
    db.close()

    keyboard = InlineKeyboardMarkup()
    for task in tasks:
        buttons = InlineKeyboardButton(
            text=task.title,
            callback_data=f"task_{task.id}"
        )
        keyboard.add(buttons)
    
    delete_all_btn = InlineKeyboardButton(text="🗑️ حذف تاریخچه", callback_data="all_delete")
    back_home_btn = InlineKeyboardButton(text="🏠 بازشگت به صفحه اصلی", callback_data="back_home")
    keyboard.add(delete_all_btn, back_home_btn)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"📝✔️ لیست تسک های انجام شده : \n",
        reply_markup=keyboard
    )


# delete all of the completed tasks
@bot.callback_query_handler(func=lambda call: call.data == "all_delete")
def delete_all_comp_task_handler(call):

    db = LocalSession()

    tasks = db.query(TaskModel).filter(
        TaskModel.status == TaskStatus.COMPLETED
    ).all()

    keyboard = InlineKeyboardMarkup()

    back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
    keyboard.add(back_home_btn)

    if not tasks:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ هیچ تسک انجام‌شده‌ای وجود ندارد.",
            reply_markup=keyboard
        )
        db.close()
        return

    for task in tasks:
        db.delete(task)

    db.commit()

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="✔️ همه وظیفه های انجام شده با موفقیت حذف شد.",
        reply_markup=keyboard
    )

    db.close()


# get detail task
@bot.callback_query_handler(func=lambda call: call.data.startswith("task"))
def get_detail_task(call):
    task_id = int(call.data.split("_")[1])
    user_id = call.from_user.id
    with state_lock:
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

        user_state[user_id] = "waiting_task_detail"

    db = LocalSession()
    task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).order_by(TaskModel.id.desc()).one()
    db.close()

    status_map = {
    TaskStatus.PENDING: "در انتظار",
    TaskStatus.COMPLETED: "انجام شده"
    }

    jalali = convert_to_jalali(task.due_date)

    response = (
        f"📋 جزییات وظیفه\n\n"
        f"📌 عنوان: {task.title}\n"
        f"📝 توضیحات: {task.description or '❌ ندارد'}\n"
        f"📆 تاریخ: {jalali['date']}\n"
        f"🕐 ساعت: {jalali['time']}\n"
        f"🔖 وضعیت: {status_map.get(task.status, task.status.value)}"
    )

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=response,
        reply_markup=task_detail_keyboard(task_id)
    )


# handler for update title of the task
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_title"))
def update_title_handler(call):
    user_id = call.from_user.id
    task_id = int(call.data.split("_")[2])
    with state_lock:
        user_temp_task[user_id] = {
            "task_id" : task_id
        }

        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

        user_state[user_id] = "waiting_new_title"

    keyboard = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_from_edit_title")
    keyboard.add(back_btn)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🔹 نام جدید وظیفه را وارد کنید :",
        reply_markup=keyboard
    )


# handler for update description of the task
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_des"))
def update_description_handler(call):
    user_id = call.from_user.id
    task_id = int(call.data.split("_")[2])
    with state_lock:
        user_temp_task[user_id] = {
            "task_id" : task_id
        }

        if user_id not in user_history:
            user_history[user_id]= []
        user_history[user_id].append(user_state[user_id])

        user_state[user_id] = "waiting_new_des"

    keyboard = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_from_edit_des")
    keyboard.add(back_btn)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="توضیحات جدید وظیفه را وارد کنید :",
        reply_markup=keyboard
    )


# handler for update due date of the task
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_due"))
def update_due_date_handler(call):
    user_id = call.from_user.id
    task_id = int(call.data.split("_")[2])
    with state_lock:
        user_temp_task[user_id] = {
            "task_id" : task_id
        } 

        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

        user_state[user_id] = "waiting_new_due"

    keyboard = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_from_edit_due")
    keyboard.add(back_btn)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="تاریخ اعلان جدید را وارد کنید : ",
        reply_markup=keyboard
    )



# handler for delete task
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))
def delete_task_handler(call):
    user_id = call.from_user.id
    task_id = int(call.data.split("_")[1])

    db = LocalSession()
    task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
    db.close()

    with state_lock:
        user_temp_task[user_id] = {
            "task_id" : task_id
        }

        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

    keyboard = InlineKeyboardMarkup()
    delete_btn = InlineKeyboardButton(text="✔️ آره", callback_data="confirm_delete")
    no_btn = InlineKeyboardButton(text="❌ نه", callback_data="no")
    keyboard.add(delete_btn, no_btn)

    user_state[user_id] = "waiting_delete_task"
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"❌ آیا از حذف وظیفه ` {task.title} ` مطمئنید ؟ ",
        reply_markup=keyboard
    )


# handler delete or not delete of the task
@bot.callback_query_handler(func=lambda call: call.data == "confirm_delete")
def delete_handler(call):
    user_id = call.from_user.id
    task_id = user_temp_task[user_id]["task_id"]
    with state_lock:
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

    db = LocalSession()
    task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
    
    if task.google_event_id:
        try:
            user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
            if user and user.access_token and user.calendar_id:
                from app.calendar_handler import CalendarHandler
                calendar = CalendarHandler(
                    access_token=user.access_token,
                    refresh_token=user.refresh_token
                )
                calendar.delete_event(
                    calendar_id=user.calendar_id,
                    event_id=task.google_event_id
                )
                print(f"✅ Event {task.google_event_id} از Calendar حذف شد")
        except Exception as e:
            print(f"❌ خطا در حذف Event از Calendar: {e}")
    
    db.delete(task)
    db.commit()
    db.close()

    keyboard = InlineKeyboardMarkup()
    back_home = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
    keyboard.add(back_home)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="✔️ وظیفه شما با موفقیت حذف شد",
        reply_markup=keyboard
    )




@bot.callback_query_handler(func=lambda call: call.data == "no")
def not_delete_task_handler(call):

    user_id = call.from_user.id
    task_id = user_temp_task[user_id]["task_id"]

    with state_lock:
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])
        user_state[user_id] = "waiting_task_detail"


    db = LocalSession()
    task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
    db.close()

    status_map = {
        TaskStatus.PENDING: "در انتظار",
        TaskStatus.COMPLETED: "انجام شده"
    }
                        
    jalali = convert_to_jalali(task.due_date)
    response = (
        f"📋 جزییات وظیفه\n\n"
        f"📌 عنوان: {task.title}\n"
        f"📝 توضیحات: {task.description or '❌ ندارد'}\n"
        f"📆 تاریخ: {jalali['date']}\n"
        f"🕐 ساعت: {jalali['time']}\n"
        f"🔖 وضعیت: {status_map.get(task.status, task.status.value)}"
    )
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=response,
        reply_markup=task_detail_keyboard(task_id)
    )



# reject handler
@bot.callback_query_handler(func=lambda call: call.data == "reject")
def reject_description_handler(call):
    user_id = call.from_user.id
    
    with state_lock:
        user_temp_task[user_id]["description"] = None
        
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])
        
        user_state[user_id] = "waiting_due_date"
    
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📆 تاریخ اعلان را وارد کنید :",
        reply_markup=add_due_date_task_keyboard()
    )



# handler for retry
@bot.callback_query_handler(func=lambda call: call.data == "retry")
def retry_handler(call):
    user_id = call.from_user.id

    with state_lock:
        if user_id in user_temp_task:
            user_temp_task[user_id].pop("due_date", None)

        user_state[user_id] = "waiting_due_date"

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="📆 تاریخ اعلان را وارد کنید :",
        reply_markup=add_due_date_task_keyboard()
    )


@bot.callback_query_handler(func=lambda call: call.data == "back_from_edit_title")
def back_from_new_title_handler(call):
    user_id = call.from_user.id

    with state_lock:
        if user_id not in user_history:
            user_history[user_id] = []
        state = user_state[user_id]

    if state == "waiting_new_title":
        previous_state = user_history[user_id].pop()
        with state_lock:
            user_state[user_id] = previous_state
            task_id = user_temp_task[user_id]["task_id"]
    
            db = LocalSession()
            task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
            db.close()
    
            status_map = {
                TaskStatus.PENDING: "در انتظار",
                TaskStatus.COMPLETED: "انجام شده"
                }
            
            jalali = convert_to_jalali(task.due_date)
            response = (
                f"📋 جزییات وظیفه\n\n"
                f"📌 عنوان: {task.title}\n"
                f"📝 توضیحات: {task.description or '❌ ندارد'}\n"
                f"📆 تاریخ: {jalali['date']}\n"
                f"🕐 ساعت: {jalali['time']}\n"
                f"🔖 وضعیت: {status_map.get(task.status, task.status.value)}"
            )

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=response,
                reply_markup=task_detail_keyboard(task_id)
            )



@bot.callback_query_handler(func=lambda call: call.data == "back_from_edit_des")
def back_from_new_des_handler(call):
    user_id = call.from_user.id

    with state_lock:
        if user_id not in user_history:
            user_history[user_id] = []
        state = user_state[user_id]

    if state == "waiting_new_des":
        previous_state = user_history[user_id].pop()
        with state_lock:
            user_state[user_id] = previous_state
            task_id = user_temp_task[user_id]["task_id"]
    
        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        db.close()
    
        status_map = {
            TaskStatus.PENDING: "در انتظار",
            TaskStatus.COMPLETED: "انجام شده"
        }
                    
        jalali = convert_to_jalali(task.due_date)
        response = (
            f"📋 جزییات وظیفه\n\n"
            f"📌 عنوان: {task.title}\n"
            f"📝 توضیحات: {task.description or '❌ ندارد'}\n"
            f"📆 تاریخ: {jalali['date']}\n"
            f"🕐 ساعت: {jalali['time']}\n"
            f"🔖 وضعیت: {status_map.get(task.status, task.status.value)}"
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=response,
            reply_markup=task_detail_keyboard(task_id)
        )




@bot.callback_query_handler(func=lambda call: call.data == "back_from_edit_due")
def back_from_new_due_handler(call):
    user_id = call.from_user.id

    with state_lock:
        if user_id not in user_history:
            user_history[user_id] = []
        state = user_state[user_id]

    if state == "waiting_new_due":
        previous_state = user_history[user_id].pop()
        with state_lock:
            user_state[user_id] = previous_state
            task_id = user_temp_task[user_id]["task_id"]
    
        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        db.close()
    
        status_map = {
            TaskStatus.PENDING: "در انتظار",
            TaskStatus.COMPLETED: "انجام شده"
        }
                            
        jalali = convert_to_jalali(task.due_date)
        response = (
            f"📋 جزییات وظیفه\n\n"
            f"📌 عنوان: {task.title}\n"
            f"📝 توضیحات: {task.description or '❌ ندارد'}\n"
            f"📆 تاریخ: {jalali['date']}\n"
            f"🕐 ساعت: {jalali['time']}\n"
            f"🔖 وضعیت: {status_map.get(task.status, task.status.value)}"
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=response,
            reply_markup=task_detail_keyboard(task_id)
        )



# back handler
@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_handler(call):
    user_id = call.from_user.id
    first_name = call.message.chat.first_name

    with state_lock:
        if user_id not in user_history:
            user_history[user_id] = []
        state = user_state[user_id]

    if state == "waiting_title":
        previous_state = user_history[user_id].pop()
        user_state[user_id] = previous_state

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"سلام {first_name} عزیز 👋\n" \
            "لطفا یکی از گزینه های زیر را انتخاب کن",
            reply_markup=start_keyboard()
        )


    elif state == "waiting_description":
        previous_state = user_history[user_id].pop()
        with state_lock:
            user_state[user_id] = previous_state

        bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🔹 نام وظیفه خود را وارد کنید :",
        reply_markup=add_title_task_keyboard()
    )
        
    
    elif state == "waiting_due_date":
        previous_state = user_history[user_id].pop()
        with state_lock:
            user_state[user_id] = previous_state

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✏️ توضیحات وظیفه خود را وارد کنید :",
            reply_markup=add_des_task_keyboard()
        )
    

    elif state == "waiting_task_list":
        previous_state = user_history[user_id].pop()
        with state_lock:
            user_state[user_id] = previous_state

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"سلام {first_name} عزیز 👋\n" \
            "لطفا یکی از گزینه های زیر را انتخاب کن",
            reply_markup=start_keyboard()
        )
    

    elif state == "waiting_task_detail":
        previous_state = user_history[user_id].pop()
        with state_lock:
            user_state[user_id] = previous_state

        db = LocalSession()
        tasks = db.query(TaskModel).filter_by(user_id=user_id).all()

        keyboard = InlineKeyboardMarkup()
        for item in tasks:
            task_button = InlineKeyboardButton(
                text=item.title,
                callback_data=f"task_{item.id}"
            )
            keyboard.add(task_button)
        
        back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")
        keyboard.add(back_btn)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📋 لیست وظایف :",
            reply_markup=keyboard
        )


    elif state == "waiting_new_due":
        previous_state = user_history[user_id].pop()
        with state_lock:
            user_state[user_id] = previous_state
            task_id = user_temp_task[user_id]["task_id"]

        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        db.close()

        response = f"""
                🔹 نام وظیفه : {task.title}
                📂 توضیحات وظیفه : {task.description}
                📆 تاریخ اعلان : {task.due_date}
            """
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=response,
            reply_markup=task_detail_keyboard(task_id)
        )



# back home handler
@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def back_home_handler(call):
    user_id = call.from_user.id
    first_name = call.message.chat.first_name

    with state_lock:
        user_state[user_id] = "main_menu"
        if user_id in user_temp_task:
            del user_temp_task[user_id]
        
        if user_id in user_history:
            user_history[user_id] = []

        bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"سلام {first_name} عزیز 👋\n" \
        "لطفا یکی از گزینه های زیر را انتخاب کن",
        reply_markup=start_keyboard()
    )



@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_handler(call):

    user_id = call.from_user.id
    
    with state_lock:
        if user_id not in user_state:
            user_state[user_id] = "main_menu"
    
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])
    
        user_state[user_id] = "waiting_help"

    keyboard = InlineKeyboardMarkup()

    back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
    keyboard.add(back_home_btn)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text = """
            🔦 **راهنمای ربات**

            سلام! 👋  
            این ربات بهت کمک میکنه وظایفت رو مدیریت کنی و یادآوری‌های به‌موقع دریافت کنی.

            ---

            📌 **ثبت‌نام در Google Calendar (اختیاری)**
            برای دریافت نوتیف از طریق Google Calendar، باید ثبت‌نام کنی.  
            اگه ثبت‌نام نکنی، باز هم میتونی از ربات استفاده کنی و نوتیف‌های تلگرام رو دریافت کنی.

            ---

            📋 **کاربردهای ربات**

            ➕ **افزودن وظیفه**  
            عنوان، توضیحات (اختیاری) و تاریخ رو وارد کن.

            📋 **لیست وظایف**  
            همه وظایفت رو ببین.

            📝✔️ **لیست وظایف انجام‌شده**  
            وظایفی که زمانشون گذشته یا انجام شدن رو ببین.

            ✏️ **ویرایش وظیفه**  
            عنوان، توضیحات یا تاریخ رو تغییر بده.

            🗑️ **حذف وظیفه**  
            وظیفه رو پاک کن.

            🔗 **ثبت‌نام در Google Calendar**  
            برای دریافت نوتیف از کلندر، ثبت‌نام کن.

            🚪 **خروج از حساب Google**  
            از حساب کلندر خارج شو.

            ---

            🔔 **نحوه نوتیف‌ها**

            **تلگرام:**
            • ۲ ساعت قبل از هر وظیفه
            • هر شب ساعت ۱۰، اگه حداقل ۱۲ ساعت تا انجام وظیفه مونده باشه

            **Google Calendar:**
            • ۲ ساعت قبل از هر وظیفه
            • ۲۴ ساعت قبل (اگه حداقل ۲۴ ساعت مونده باشه)
            • ۷۲ ساعت قبل (اگه حداقل ۷۲ ساعت مونده باشه)

            ---

            📞 **پشتیبانی**  
            اگه سوال یا مشکلی داری، میتونی با پشتیبانی در ارتباط باشی.
            """,
        reply_markup=keyboard
    )




# text handlers
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    with state_lock:
        state = user_state.get(user_id)

    if state == "waiting_title":
        with state_lock:
            user_temp_task[user_id] = {
                "title" : message.text
            }

            if user_id not in user_history:
                user_history[user_id] = []
            user_history[user_id].append(user_state[user_id])

            user_state[user_id] = "waiting_description"
        bot.send_message(
            chat_id=message.chat.id,
            text="✏️ توضیحات وظیفه خود را وارد کنید :",
            reply_markup=add_des_task_keyboard()
        )
    
    
    elif state == "waiting_description":
        with state_lock:
            user_temp_task[user_id]["description"] = message.text

            if user_id not in user_history:
                user_history[user_id] = []
            user_history[user_id].append(user_state[user_id])

            user_state[user_id] = "waiting_due_date"

        bot.send_message(
            chat_id=message.chat.id,
            text="📆 تاریخ اعلان را وارد کنید :",
            reply_markup=add_due_date_task_keyboard()
        )


    elif state == "waiting_due_date":
        try:
            due_date = parse_date(message.text)

        except Exception as e:
            keyboard = InlineKeyboardMarkup()
            retry_btn = InlineKeyboardButton(text="🔄️ تلاش مجدد", callback_data="retry")
            keyboard.add(retry_btn)

            bot.send_message(
                chat_id=message.chat.id,
                text="❌ خطا در تحلیل تاریخ; لطفا تاریخ را مجدد وارد کنید!",
                reply_markup=keyboard
            )
            return

        keyboard = InlineKeyboardMarkup()
        back_home_btn = InlineKeyboardButton(text="🔄️ تلاش مجدد", callback_data="retry")
        keyboard.add(back_home_btn)

        if due_date is None:
            bot.send_message(
                chat_id=message.chat.id,
                text="❌ تاریخ وارد شده معتبر نیست. تاریخ را دوباره وارد کنید.",
                reply_markup=keyboard
            )
            return 
        
        user_temp_task[user_id]["due_date"] = message.text
        due_date_utc = due_date.astimezone(timezone.utc)

        keyboard = InlineKeyboardMarkup()
        back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
        keyboard.add(back_home_btn)

        db = LocalSession()
        task = TaskModel(
            user_id = user_id,
            title = user_temp_task[user_id]["title"],
            description = user_temp_task[user_id]["description"],
            due_date = due_date_utc
        )
        db.add(task)
        db.flush()
        
        user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
        
        if user and user.access_token:
            try:
                from app.calendar_handler import CalendarHandler
                
                calendar = CalendarHandler(
                    access_token=user.access_token,
                    refresh_token=user.refresh_token
                )
                
                google_event_id = calendar.create_event(
                calendar_id=user.calendar_id,
                summary=user_temp_task[user_id]["title"],
                description=user_temp_task[user_id]["description"],
                start_time=due_date_utc,
                end_time=due_date_utc + timedelta(hours=1),
                reminder_minutes=120
            )
                
                task.google_event_id = google_event_id
                
            except Exception as e:
                import traceback
                traceback.print_exc()
        else:
            print("ℹ️ کاربر در Google Calendar لاگین نیست، فقط در دیتابیس ذخیره شد")

        db.commit()
        db.close()

        bot.send_message(
            chat_id=message.chat.id,
            text="✔️ وظیفه شما با موفقیت ثبت شد",
            reply_markup=keyboard
        )

    
    elif state == "waiting_new_title":
        with state_lock:
            task_id = user_temp_task[user_id]["task_id"]
            if user_id not in user_history:
                user_history[user_id] = []
            user_history[user_id].append(user_state[user_id])

        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        task.title = message.text
        db.commit()
        
        if task.google_event_id:
            try:
                user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
                if user and user.access_token and user.calendar_id:
                    from app.calendar_handler import CalendarHandler
                    calendar = CalendarHandler(
                        access_token=user.access_token,
                        refresh_token=user.refresh_token
                    )
                    calendar.update_event(
                        calendar_id=user.calendar_id,
                        event_id=task.google_event_id,
                        summary=message.text
                    )
                    print(f"✅ Event {task.google_event_id} در Calendar به‌روز شد")
            except Exception as e:
                print(f"❌ خطا در ویرایش Event: {e}")
        
        db.close()

        keyboard = InlineKeyboardMarkup()
        back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
        keyboard.add(back_home_btn)

        bot.send_message(
            chat_id=message.chat.id,
            text="✔️ نام وظیفه با موفقیت ویرایش شد",
            reply_markup=keyboard
        )

    
    elif state == "waiting_new_des":
        with state_lock:
            task_id = user_temp_task[user_id]["task_id"]
            if user_id not in user_history:
                user_history[user_id] = []
            user_history[user_id].append(user_state[user_id])

        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        task.description = message.text
        db.commit()
        
        if task.google_event_id:
            try:
                user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
                if user and user.access_token and user.calendar_id:
                    from app.calendar_handler import CalendarHandler
                    calendar = CalendarHandler(
                        access_token=user.access_token,
                        refresh_token=user.refresh_token
                    )
                    calendar.update_event(
                        calendar_id=user.calendar_id,
                        event_id=task.google_event_id,
                        description=message.text
                    )
                    print(f"✅ Event {task.google_event_id} در Calendar به‌روز شد")
            except Exception as e:
                print(f"❌ خطا در ویرایش Event: {e}")
        
        db.close()

        keyboard = InlineKeyboardMarkup()
        back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
        keyboard.add(back_home_btn)

        bot.send_message(
            chat_id=message.chat.id,
            text="✔️ توضیحات با موفقیت ویرایش شد",
            reply_markup=keyboard
        )

    
    elif state == "waiting_new_due":
        with state_lock:
            task_id = user_temp_task[user_id]["task_id"]
            if user_id not in user_history:
                user_history[user_id] = []
            user_history[user_id].append(user_state[user_id])

        try:
            new_due_date = parse_date(message.text)
            if new_due_date is None:
                raise ValueError
        except:
            if user_id in user_temp_task:
                user_temp_task[user_id].pop("due_date", None)
            keyboard = InlineKeyboardMarkup()
            back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
            keyboard.add(back_home_btn)
            bot.send_message(
                chat_id=message.chat.id,
                text="❌ خطا در تحلیل تاریخ! لطفاً تاریخ را به فرمت صحیح وارد کنید.",
                reply_markup=keyboard
            )
            return

        new_due_date_utc = new_due_date.astimezone(timezone.utc)

        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        task.due_date = new_due_date_utc
        db.commit()
        
        if task.google_event_id:
            try:
                user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
                if user and user.access_token and user.calendar_id:
                    from app.calendar_handler import CalendarHandler
                    calendar = CalendarHandler(
                        access_token=user.access_token,
                        refresh_token=user.refresh_token
                    )
                    calendar.update_event(
                        calendar_id=user.calendar_id,
                        event_id=task.google_event_id,
                        start_time=new_due_date_utc,
                        end_time=new_due_date_utc + timedelta(hours=1)
                    )
                    print(f"✅ Event {task.google_event_id} در Calendar به‌روز شد")
            except Exception as e:
                print(f"❌ خطا در ویرایش Event: {e}")
        
        db.close()

        keyboard = InlineKeyboardMarkup()
        back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
        keyboard.add(back_home_btn)

        bot.send_message(
            chat_id=message.chat.id,
            text="✔️ تاریخ اعلان با موفقیت ویرایش شد",
            reply_markup=keyboard
        )

    
    else:
        current_datetime = datetime.now()
        try:
            parsed_task = parse_task(message.text)
        except:

            if user_id in user_temp_task:
                user_temp_task[user_id].pop()

            keyboard = InlineKeyboardMarkup()
            back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
            keyboard.add(back_home_btn)

            bot.send_message(
                chat_id=message.chat.id,
                text=f"❌ خطا در ارتباط با سرویس تحلیل تاریخ! لطفاً اتصال اینترنت یا VPN خود را بررسی کنید و دوباره تلاش کنید.",
                reply_markup=keyboard
            )
            return
        
        if parsed_task is None:
            return 
        task = calculate_task(current_datetime=current_datetime, parsed_task=parsed_task)
        if task is None:
            return
        
        due_date = task["due_date"]
        due_date_utc = due_date.astimezone(timezone.utc)
        
        db = LocalSession()
        new_task = TaskModel(
            user_id=user_id,
            title=task["title"],
            description=task["description"],
            due_date=due_date_utc
        )
        db.add(new_task)
        db.flush()
        
        user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
        
        if user and user.access_token and user.calendar_id:
            try:
                from app.calendar_handler import CalendarHandler
                
                calendar = CalendarHandler(
                    access_token=user.access_token,
                    refresh_token=user.refresh_token
                )
                
                google_event_id = calendar.create_event(
                    calendar_id=user.calendar_id,
                    summary=new_task.title,
                    description=new_task.description or "",
                    start_time=due_date_utc,
                    end_time=due_date_utc + timedelta(hours=1),
                    reminder_minutes=120
                )
                
                new_task.google_event_id = google_event_id
                
            except Exception as e:
                import traceback
                traceback.print_exc()
        else:
            print("ℹ️ کاربر در Google Calendar لاگین نیست، فقط در دیتابیس ذخیره شد")

        task_id = new_task.id
        
        db.commit()
        db.close()

        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        db.close()
        
        status_map = {
            TaskStatus.PENDING: "در انتظار",
            TaskStatus.COMPLETED: "انجام شده"
            }
        
        jalali = convert_to_jalali(task.due_date)
        
        response = (
            f"📋 جزییات وظیفه\n\n"
            f"📌 عنوان: {task.title}\n"
            f"📝 توضیحات: {task.description or '❌ ندارد'}\n"
            f"📆 تاریخ: {jalali['date']}\n"
            f"🕐 ساعت: {jalali['time']}\n"
            f"🔖 وضعیت: {status_map.get(task.status, task.status.value)}"
        )

        with state_lock:
            if user_id not in user_history:
                user_history[user_id] = []
            user_history[user_id].append(user_state.get(user_id, "main_menu"))
            user_state[user_id] = "main_menu"
        
        keyboard = InlineKeyboardMarkup()
        back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
        keyboard.add(back_home_btn)
        
        bot.send_message(
            chat_id=message.chat.id,
            text=response,
            reply_markup=keyboard
        )