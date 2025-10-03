import os
from cerebras.cloud.sdk import Cerebras
from dotenv import load_dotenv

load_dotenv()

client = Cerebras(
    api_key=os.environ.get("CEREBRAS_API_KEY"),  # This is the default and can be omitted
)


chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "What  is the capital of India?",
            "max_tokens": 5,
        }
    ],
    model="llama3.1-8b",
)

print(chat_completion.choices[0].message.content)