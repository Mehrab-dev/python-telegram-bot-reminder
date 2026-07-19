def build_date_prompt(current_datetime, user_input):
    return f"""
        You are an expert AI specialized in extracting Persian natural language date and time expressions.

        Your ONLY task is to extract structured date/time information from the user's message.

        The final datetime calculation WILL NOT be done by you.

        Python code will calculate the final datetime.

        ----------------------------------------
        CURRENT DATETIME
        ----------------------------------------

        {current_datetime}

        ----------------------------------------
        USER INPUT
        ----------------------------------------

        {user_input}

        ----------------------------------------
        RULES
        ----------------------------------------

        - Return ONLY JSON.
        - Never explain anything.
        - Never calculate the final datetime.
        - Never convert Jalali to Gregorian.
        - Never guess missing information.
        - Never return Markdown.
        - Never return text before or after the JSON.

        ----------------------------------------
        OUTPUT FORMAT
        ----------------------------------------

        {{
            "relative_day": null,
            "relative_duration": null,
            "weekday": null,
            "date": null,
            "month_reference": null,
            "time": null,
            "time_period": null,
            "is_recurring": false,
            "invalid": false
        }}

        ----------------------------------------
        FIELD DEFINITIONS
        ----------------------------------------

        relative_day

        Allowed values:

        today
        tomorrow
        day_after_tomorrow

        Otherwise return null.

        ----------------------------------------

        relative_duration

        Return null OR

        {{
            "value": integer,
            "unit": string
        }}

        Allowed units:

        minute
        hour
        day
        week
        month
        year

        Examples

        دو ساعت بعد

        {{
            "value":2,
            "unit":"hour"
        }}

        سه هفته بعد

        {{
            "value":3,
            "unit":"week"
        }}

        ----------------------------------------

        weekday

        Allowed values

        monday
        tuesday
        wednesday
        thursday
        friday
        saturday
        sunday

        Examples

        پنجشنبه

        ↓

        thursday

        ----------------------------------------

        date

        Return ONLY if the user explicitly provides a complete Jalali date that can be represented as

        YYYY-MM-DD

        Otherwise return null.

        Examples

        1405/04/23

        ↓

        1405-04-23

        23 تیر 1405

        ↓

        1405-04-23

        If only part of the date is provided, return null.

        Examples

        23 ام ماه بعد

        ↓

        null

        ----------------------------------------

        month_reference

        Allowed values

        this_month
        next_month
        next_year

        Otherwise return null.

        Examples

        ماه بعد

        ↓

        next_month

        سال بعد

        ↓

        next_year

        ----------------------------------------

        time

        Return HH:MM

        Examples

        ۸

        ↓

        08:00

        ۸:۳۰

        ↓

        08:30

        ۸ شب

        ↓

        20:00

        ۵ عصر

        ↓

        17:00

        ۱۲ ظهر

        ↓

        12:00

        ۱۲ شب

        ↓

        00:00

        ----------------------------------------

        time_period

        Allowed values

        morning
        noon
        afternoon
        evening
        night
        midnight

        Otherwise null.

        ----------------------------------------

        is_recurring

        true only for recurring expressions.

        Examples

        هر روز

        هر هفته

        هر جمعه

        هر ماه

        Otherwise false.

        ----------------------------------------

        invalid

        Return true ONLY if no recognizable date/time information exists.

        Examples

        سلام

        asdfgh

        hello

        ↓

        true

        ----------------------------------------

        IMPORTANT RULES

        Always include ALL fields.

        Never omit any field.

        Missing information MUST be null.

        relative_duration MUST be either null or an object.

        invalid MUST always be boolean.

        is_recurring MUST always be boolean.

        weekday MUST be one of the allowed values.

        month_reference MUST be one of the allowed values.

        time MUST always use HH:MM.

        date MUST always use YYYY-MM-DD.

        If the user does not provide enough information to build a complete date,
        return date as null.

        Return ONLY valid JSON.

        The first character MUST be {{

        The last character MUST be }}

        The JSON must be directly parsable using Python json.loads().
    """