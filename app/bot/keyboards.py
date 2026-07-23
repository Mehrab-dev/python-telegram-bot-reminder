from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_keyboard():
    keyboard = InlineKeyboardMarkup()
    
    add_task_btn = InlineKeyboardButton(text="➕ افزودن وظیفه", callback_data="add_task")
    list_task_btn = InlineKeyboardButton(text="📋 لیست وظایف", callback_data="list_task")
    comp_list_task_btn = InlineKeyboardButton(text="📝✔️ لیست وظایف انجام شده", callback_data="comp_list")
    help_btn = InlineKeyboardButton(text=" 🔦 راهنما", callback_data="help")
    google_btn = InlineKeyboardButton("🔗 ثبت‌نام در Google Calendar", callback_data="google_login")
    logout_btn = InlineKeyboardButton("🚪 خروج از حساب Google", callback_data="logout")
    support_btn = InlineKeyboardButton(text="📞 ارتباط با پشتیبانی", url="https://t.me/Mh1RBa")


    keyboard.add(add_task_btn, list_task_btn)
    keyboard.add(comp_list_task_btn, help_btn)
    keyboard.add(google_btn, logout_btn)
    keyboard.add(support_btn)

    return keyboard


def add_title_task_keyboard():
    keyboard = InlineKeyboardMarkup()

    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")
    keyboard.add(back_btn)

    return keyboard


def add_des_task_keyboard():
    keyboard = InlineKeyboardMarkup()

    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")
    rej_btn = InlineKeyboardButton(text="رد کردن", callback_data="reject")
    keyboard.add(back_btn, rej_btn)

    return keyboard


def add_due_date_task_keyboard():
    keyboard = InlineKeyboardMarkup()

    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")
    keyboard.add(back_btn)
    
    return keyboard


def task_detail_keyboard(task_id):
    keyboard = InlineKeyboardMarkup()

    edit_title_btn = InlineKeyboardButton(text="✏️ ویرایش نام وظیفه", callback_data=f"edit_title_{task_id}")
    edit_des_btn = InlineKeyboardButton(text="✏️ ویرایش توضیحات وظیفه", callback_data=f"edit_des_{task_id}")
    edit_due_date_btn = InlineKeyboardButton(text="✏️ ویرایش تاریخ اعلان", callback_data=f"edit_due_{task_id}")
    delete_btn = InlineKeyboardButton(text="🗑️ حذف وظیفه", callback_data=f"delete_{task_id}")
    back_btn = InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")
    keyboard.add(edit_title_btn, edit_des_btn)
    keyboard.add(edit_due_date_btn, delete_btn)
    keyboard.add(back_btn)

    return keyboard