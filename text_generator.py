from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

prompt = "Hello Gemini! How are you today? And also, give me a random word"

def call_response():
    global response
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config = {
            "temperature": 0.7
        }
    )

    return response