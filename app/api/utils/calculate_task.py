from datetime import datetime

from app.api.utils.calculate_date import calculate_datetime

def calculate_task(current_datetime: datetime, parsed_task: dict):

    due_date = calculate_datetime(
        current_datetime=current_datetime,
        parsed_date=parsed_task["date"]
    )
    
    if due_date is None:
        return None

    return {
        "title": parsed_task["title"],
        "description": parsed_task["description"],
        "due_date": due_date
    }