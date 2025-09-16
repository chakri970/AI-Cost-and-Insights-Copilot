# api/app/groq_test.py
import os
from dotenv import load_dotenv
from groq import Groq

def test_groq():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ No GROQ_API_KEY found in env")
        return
    client = Groq(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello from Groq"}],
            model="llama-3.3-70b-versatile"
        )
        print("✅ Groq API works. Response:", resp.choices[0].message.content)
    except Exception as e:
        print("❌ Groq API error:", e)

if __name__ == "__main__":
    test_groq()
