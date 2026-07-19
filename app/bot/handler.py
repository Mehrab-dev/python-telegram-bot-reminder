from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import timezone
from datetime import datetime

from app.bot.client import bot
from app.bot.keyboards import (start_keyboard, add_title_task_keyboard, add_des_task_keyboard, add_due_date_task_keyboard, task_detail_keyboard)
from app.database.database import LocalSession
from app.database.models import TaskModel
from app.api.parsers.date_parser import parse_date
from app.api.parsers.task_parser import parse_task
from app.api.utils.calculate_task import calculate_task


user_state = {}
user_temp_task = {}
user_history = {}


@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.from_user.id

    if user_id not in user_history:
        user_history[user_id] = []

    user_id = message.chat.id
    user_state[user_id] = "main_menu"
    first_name = message.chat.first_name

    bot.send_message(
        chat_id=message.chat.id,
        text=f"سلام {first_name} عزیز 👋" \
        "لطفا یکی از گزینه های زیر را انتخاب کن",
        reply_markup=start_keyboard()
    )


# handler for add task
@bot.callback_query_handler(func=lambda call: call.data == "add_task")
def add_task_handler(call):
    user_id = call.from_user.id

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


# handler for list task
@bot.callback_query_handler(func=lambda call: call.data == "list_task")
def list_task_handler(call):
    user_id = call.from_user.id

    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(user_state[user_id])

    user_state[user_id] = "waiting_task_list"

    db = LocalSession()
    tasks = db.query(TaskModel).filter_by(user_id=user_id).order_by(TaskModel.id.desc()).all()
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


# get detail task
@bot.callback_query_handler(func=lambda call: call.data.startswith("task"))
def get_detail_task(call):
    task_id = int(call.data.split("_")[1])
    user_id = call.from_user.id

    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(user_state[user_id])

    user_state[user_id] = "waiting_task_detail"

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


# handler for update title of the task
@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_title"))
def update_title_handler(call):
    user_id = call.from_user.id
    task_id = int(call.data.split("_")[2])
    user_temp_task[user_id] = {
        "task_id" : task_id
    }

    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(user_state[user_id])

    user_state[user_id] = "waiting_new_title"

    keyboard = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")
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
    user_temp_task[user_id] = {
        "task_id" : task_id
    }

    if user_id not in user_history:
        user_history[user_id]= []
    user_history[user_id].append(user_state[user_id])

    user_state[user_id] = "waiting_new_des"

    keyboard = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")
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
    user_temp_task[user_id] = {
        "task_id" : task_id
    } 

    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(user_state[user_id])

    user_state[user_id] = "waiting_new_due"

    keyboard = InlineKeyboardMarkup()
    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")
    keyboard.add(back_btn)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="تاریخ اعلان جدید را وارد کنید : ",
        reply_markup=keyboard
    )


# back handler
@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_handler(call):
    user_id = call.from_user.id
    if user_id not in user_history:
        user_history[user_id] = []
    state = user_state[user_id]

    if state == "waiting_title":
        previous_state = user_history[user_id].pop()
        user_state[user_id] = previous_state

        first_name = call.message.chat.first_name

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"سلام {first_name} عزیز 👋" \
            "لطفا یکی از گزینه های زیر را انتخاب کن",
            reply_markup=start_keyboard()
        )


    elif state == "waiting_description":
        previous_state = user_history[user_id].pop()
        user_state[user_id] = previous_state

        bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="🔹 نام وظیفه خود را وارد کنید :",
        reply_markup=add_title_task_keyboard()
    )
        
    
    elif state == "waiting_due_date":
        previous_state = user_history[user_id].pop()
        user_state[user_id] = previous_state

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✏️ توضیحات وظیفه خود را وارد کنید :",
            reply_markup=add_des_task_keyboard()
        )
    

    elif state == "waiting_task_list":
        previous_state = user_history[user_id].pop()
        user_state[user_id] = previous_state
        first_name = call.message.chat.first_name

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"سلام {first_name} عزیز 👋" \
            "لطفا یکی از گزینه های زیر را انتخاب کن",
            reply_markup=start_keyboard()
        )
    

    elif state == "waiting_task_detail":
        previous_state = user_history[user_id].pop()
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
    

    elif state == "waiting_new_title":
        previous_state = user_history[user_id].pop()
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
    

    elif state == "waiting_new_des":
        previous_state = user_history[user_id].pop()
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


    elif state == "waiting_new_due":
        previous_state = user_history[user_id].pop()
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

    user_state[user_id] = "main_menu"
    
    if user_id in user_temp_task:
        del user_temp_task[user_id]
    
    if user_id in user_history:
        user_history[user_id] = []

        bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"سلام {first_name} عزیز 👋" \
        "لطفا یکی از گزینه های زیر را انتخاب کن",
        reply_markup=start_keyboard()
    )


# text handlers
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    state = user_state.get(user_id)

    if state == "waiting_title":
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
        due_date = parse_date(message.text)

        keyboard = InlineKeyboardMarkup()
        back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
        keyboard.add(back_home_btn)

        if due_date is None:
            bot.send_message(
                chat_id=message.chat.id,
                text="❌ تاریخ وارد شده معتبر نیست . تاریخ را دوباره وارد کنید.",
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
        db.commit()
        db.close()

        bot.send_message(
            chat_id=message.chat.id,
            text="✔️ وظیفه شما با موفقیت ثبت شد",
            reply_markup=keyboard
        )

    
    elif state == "waiting_new_title":
        task_id = user_temp_task[user_id]["task_id"]

        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        task.title = message.text
        db.commit()
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
        task_id = user_temp_task[user_id]["task_id"]
        
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        task.description = message.text
        db.commit()
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
        task_id = user_temp_task[user_id]["task_id"]
        
        if user_id not in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state[user_id])

        db = LocalSession()
        task = db.query(TaskModel).filter_by(id=task_id, user_id=user_id).one()
        task.due_date = message.text
        db.commit()
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
        parsed_task = parse_task(message.text)
        if parsed_task is None:
            return 
        print(parsed_task)
        task = calculate_task(current_datetime=current_datetime,parsed_task=parsed_task)
        if task is None:
            return
        
        keyboard = InlineKeyboardMarkup()
        back_home_btn = InlineKeyboardButton(text="🏠 بازگشت به صفحه اصلی", callback_data="back_home")
        keyboard.add(back_home_btn)

        due_date = task["due_date"]
        due_date_utc = due_date.astimezone(timezone.utc)

        db = LocalSession()
        new_task = TaskModel(
            user_id = user_id,
            title = task["title"],
            description = task["description"],
            due_date = due_date_utc
        )
        db.add(new_task)
        db.commit()
        db.close()

        response = f"""
                ✔️ وظیفه با موفقیت اضافه شد :
                🔹 نام وظیفه : {task["title"]}
                📂 توضیحات وظیفه : {task["description"] or '❌ ندارد'}
                📆 تاریخ اعلان وظیفه : {task["due_date"]}
            """
    
        if not user_id in user_history:
            user_history[user_id] = []
        user_history[user_id].append(user_state.get(user_id, "main_menu"))
        user_state[user_id] = "main_menu"

        bot.send_message(
            chat_id=message.chat.id,
            text=response,
            reply_markup=keyboard
        )