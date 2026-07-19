import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(
    api_key = GROQ_API_KEY
)

def generate_response(prompt):
    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages = [
            {
                "role" : "user",
                "content" : prompt
            }
        ],
        temperature = 0,
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content