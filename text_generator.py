from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPEN_ROUTER_API_KEY")
)

def call_response(**kwargs):
    prompt = kwargs.get('prompt', None)
    if prompt == None:
        prompt = "Hello GPT! How are you today? And also, give me a random word. Use plain text."
    else:
        prompt = f'Дай описание места в Москве под названием "{prompt}". Уделяй больше акцент на архитектуру и историю. Не используй слишком сложный текст. Пиши чисто текстом, с абзацами.'
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-maverick:free",
        messages=[
        {
        "role": "user",
        "content": prompt
        }
        ]
    )
    return completion.choices[0].message.content