from datetime import datetime
import json
from json import JSONDecodeError

from app.api.prompts.task_prompt import build_task_prompt
from app.api.groq_client import generate_response
from app.api.validations.task_validation import validation_task
from app.api.utils.calculate_task import calculate_task


def parse_task(user_input):
    current_datetime = datetime.now()

    prompt = build_task_prompt(
        current_datetime=current_datetime,
        user_input=user_input
    )

    response = generate_response(prompt)
    if response is None:
        return None
    
    try:
        parsed_response = json.loads(response)

        if not validation_task(parsed_response):
            return None
        
        return parsed_response

    except JSONDecodeError:
        return None

