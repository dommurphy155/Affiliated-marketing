import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_content():
    prompt = "Generate a short, viral marketing pitch for a trending digital product."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()
