import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello, testing connectivity."},
        ],
        max_tokens=10
    )
    print("DeepSeek Connectivity: SUCCESS")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"DeepSeek Connectivity: FAILED - {e}")
