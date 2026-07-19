from datetime import datetime
import json
from json import JSONDecodeError

from app.api.prompts.date_prompt import build_date_prompt
from app.api.groq_client import generate_response
from app.api.validations.date_validation import validation_datetime
from app.api.utils.calculate_date import calculate_datetime


def parse_date(user_input):
    current_datetime = datetime.now()

    prompt = build_date_prompt(
        user_input=user_input,
        current_datetime=current_datetime
    )
    response = generate_response(prompt)

    if response is None:
        return None

    try:
        parsed_response = json.loads(response)

        if not validation_datetime(parsed_response):
            return None
        
        return calculate_datetime(
            current_datetime=current_datetime,
            parsed_date=parsed_response
        )

    except JSONDecodeError:
        return None