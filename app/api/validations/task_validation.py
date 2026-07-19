from datetime import datetime


REQUIRED_FIELDS = {
    "title",
    "description",
    "date",
    "invalid"
}

REQUIRED_DATE_FIELDS = {
    "relative_day",
    "relative_duration",
    "weekday",
    "date",
    "month_reference",
    "time",
    "time_period",
    "is_recurring"
}

VALID_UNITS = {
    "minute",
    "hour",
    "day",
    "week",
    "month",
    "year"
}

VALID_RELATIVE_DAY = {
    "today",
    "tomorrow",
    "day_after_tomorrow"
}

VALID_WEEK_DAY = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday"
}

VALID_MONTH_REFERENCE = {
    "this_month",
    "next_month",
    "next_year"
}

VALID_TIME_PERIOD = {
    "morning",
    "noon",
    "afternoon",
    "evening",
    "night",
    "midnight"
}



def validation_json_structure(data):
    if not isinstance(data, dict):
        return False
    if not set(data.keys()) == REQUIRED_FIELDS:
        return False
    if not isinstance(data["date"], dict):
        return False
    if not set(data["date"].keys()) == REQUIRED_DATE_FIELDS:
        return False
    
    return True



def validation_data_types(data):
    if data["title"] is not None and not isinstance(data["title"], str):
        return False
    if data["description"] is not None and not isinstance(data["description"], str):
        return False
    if data["date"] is not None and not isinstance(data["date"], dict):
        return False
    if data["date"]["relative_day"] is not None and not isinstance(data["date"]["relative_day"], str):
        return False
    
    duration = data["date"]["relative_duration"]
    if duration is not None:
        if not isinstance(duration, dict):
            return False
        if "value" not in duration:
            return False
        if "unit" not in duration:
            return False
        if not isinstance(duration["value"], int):
            return False
        if not isinstance(duration["unit"], str):
            return False
        if duration["unit"] not in VALID_UNITS:
            return False
        if set(duration.keys()) != {"value", "unit"}:
            return False
        
    if data["date"]["weekday"] is not None and not isinstance(data["date"]["weekday"], str):
        return False
    if data["date"]["date"] is not None and not isinstance(data["date"]["date"], str):
        return False
    if data["date"]["month_reference"] is not None and not isinstance(data["date"]["month_reference"], str):
        return False
    if data["date"]["time"] is not None and not isinstance(data["date"]["time"], str):
        return False
    if data["date"]["time_period"] is not None and not isinstance(data["date"]["time_period"], str):
        return False
    if data["date"]["is_recurring"] is not None and not isinstance(data["date"]["is_recurring"], bool):
        return False
    if not isinstance(data["invalid"], bool):
        return False
    
    return True


def validation_allowed_values(data):
    if (data["date"]["relative_day"] is not None and data["date"]["relative_day"] not in VALID_RELATIVE_DAY):
        return False
    if (data["date"]["weekday"] is not None and data["date"]["weekday"] not in VALID_WEEK_DAY):
        return False
    if (data["date"]["month_reference"] is not None and data["date"]["month_reference"] not in VALID_MONTH_REFERENCE):
        return False
    if (data["date"]["time_period"] is not None and data["date"]["time_period"] not in VALID_TIME_PERIOD):
        return False
    
    return True
    

def validation_time(data):
    if data["date"]["time"] is None:return True
    try:
        datetime.strptime(data["date"]["time"], "%H:%M")
        return True
    except ValueError:
        return False


def validation_date(data):
    if data["date"]["date"] is None:
        return True
    try:
        datetime.strptime(data["date"]["date"], "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validation_logic(data):

    if data["invalid"]:
        if (
            data["date"]["relative_day"] is not None
            or data["date"]["weekday"] is not None
            or data["date"]["date"] is not None
            or data["date"]["time"] is not None
        ):
            return False
        return True

    count = 0

    if data["date"]["relative_day"] is not None:
        count += 1
    if data["date"]["weekday"] is not None:
        count += 1
    if data["date"]["date"] is not None:
        count += 1
    if count > 1:
        return False

    return True


def validation_task(data):
    if not validation_json_structure(data):
        return False
    if not validation_data_types(data):
        return False
    if not validation_allowed_values(data):
        return False
    if not validation_time(data):
        return False
    if not validation_date(data):
        return False
    if not validation_logic(data):
        return False
    
    return True