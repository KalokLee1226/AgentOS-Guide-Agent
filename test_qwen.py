import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("DASHSCOPE_API_KEY")

print("API Key loaded:", bool(api_key))

client = OpenAI(
    api_key=api_key,
    base_url="https://maas.qianwenaiapi.com/compatible-mode/v1",
)

response = client.chat.completions.create(
    model="qwen3.8-omni-flash",
    messages=[
        {
            "role": "user",
            "content": "你好，请只回复：模型连接成功"
        }
    ],
)

print(response.choices[0].message.content)