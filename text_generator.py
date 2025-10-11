from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

prompt = "Hello Gemini! How are you today?"

response = client.models.generate_content(
    model="gemini-2.5-pro", #gemini-2.5-pro has only 100 requests for free per day
    contents=prompt,
    config = {
        "temperature": 0.7
    }
)