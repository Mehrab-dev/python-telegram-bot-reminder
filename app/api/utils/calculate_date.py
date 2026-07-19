from datetime import datetime, timedelta

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def calculate_datetime(current_datetime: datetime, parsed_date: dict):

    target_datetime = current_datetime

    if parsed_date["relative_day"] == "today":
        target_datetime = current_datetime

    elif parsed_date["relative_day"] == "tomorrow":
        target_datetime = current_datetime + timedelta(days=1)

    elif parsed_date["relative_day"] == "day_after_tomorrow":
        target_datetime = current_datetime + timedelta(days=2)

    elif parsed_date["relative_duration"] is not None:

        duration = parsed_date["relative_duration"]

        kwargs = {
            f"{duration['unit']}s": duration["value"]
        }

        target_datetime = current_datetime + timedelta(**kwargs)


    elif parsed_date["date"] is not None:
        pass

    elif parsed_date["month_reference"] is not None:
        pass

    elif parsed_date["weekday"] is not None:

        target_weekday = WEEKDAYS[parsed_date["weekday"]]

        days_ahead = target_weekday - current_datetime.weekday()

        if days_ahead <= 0:
            days_ahead += 7

        target_datetime = current_datetime + timedelta(days=days_ahead)

    else:
        return None

    if parsed_date["time"] is not None:
        hour, minute = map(int, parsed_date["time"].split(":"))
        target_datetime = target_datetime.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

    elif parsed_date["time_period"] is not None:

        DEFAULT_TIMES = {
            "morning": (9, 0),
            "noon": (12, 0),
            "afternoon": (15, 0),
            "evening": (18, 0),
            "night": (21, 0),
            "midnight": (0, 0),
        }

        hour, minute = DEFAULT_TIMES[parsed_date["time_period"]]

        target_datetime = target_datetime.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

    return target_datetime