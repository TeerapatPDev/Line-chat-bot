import os

import requests

from dotenv import load_dotenv

# โหลด env
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

def call_ai(text):
    url = "https://api.groq.com/openai/v1/chat/completions"

    food_data = """
    ข้าว: ข้าวผัด, ข้าวมันไก่
    เส้น: ผัดไทย, ก๋วยเตี๋ยว
    ของแซ่บ: ส้มตำ
    """

    prompt = f"""
    คุณคือ AI แนะนำอาหาร

    ให้เลือกอาหารจาก list นี้เท่านั้น:
    {food_data}

    ถ้าผู้ใช้พูดไม่ชัด ให้เดาและแนะนำอาหาร 2 เมนู
    ตอบสั้น ๆ

    user: {text}
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",   # ฟรีและเร็ว
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        res = requests.post(url, headers=headers, json=data)

        if res.status_code != 200:
            print("STATUS:", res.status_code)
            print("ERROR:", res.text)
            return "ตอนนี้ AI มีปัญหา ลองใหม่อีกครั้งนะ 😅"

        return res.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("EXCEPTION:", e)
        return "ระบบมีปัญหาเล็กน้อย ลองใหม่อีกครั้งนะครับ 🙏"


if __name__ == "__main__":
    while True:
        text = input("พิมพ์: ")
        result = call_ai(text)
        print("AI:", result)