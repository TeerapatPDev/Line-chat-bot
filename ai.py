import os
import json
import random
import requests

from dotenv import load_dotenv

# ================== LOAD ENV ==================
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

# ================== LOAD DATA ==================
with open("data/foods.json", "r", encoding="utf-8") as f:
    foods = json.load(f)

with open("data/shops.json", "r", encoding="utf-8") as f:
    shops = json.load(f)


# ================== PREPARE DATA ==================
def get_all_foods():
    all_foods = []
    for f in foods.values():
        all_foods.extend([item["name"] for item in f])
    return list(set(all_foods))


def get_all_shops():
    return [s["name"] for s in shops.values()]


ALL_FOODS = get_all_foods()
ALL_SHOPS = get_all_shops()


# ================== BUILD PROMPT ==================
def build_prompt(user_text):
    sample_foods = random.sample(ALL_FOODS, min(15, len(ALL_FOODS)))
    sample_shops = random.sample(ALL_SHOPS, min(5, len(ALL_SHOPS)))

    return f"""
คุณคือ AI สำหรับเลือกอาหารและร้านอาหารจากรายการที่กำหนดเท่านั้น
ต้องตอบเป็น JSON เท่านั้น
ห้ามคิดเมนูใหม่
ถ้าไม่เกี่ยว → {{ "type": "unknown" }}

รูปแบบ:

อาหาร:
{{ "type": "food", "items": ["ชื่ออาหาร1", "ชื่ออาหาร2", "ชื่ออาหาร3"], "intro_text": "ข้อความนำสำหรับ flex message" }}

ร้าน:
{{ "type": "shop", "items": ["ชื่อร้าน1", "ชื่อร้าน2"], "intro_text": "ข้อความนำสำหรับ flex message" }}

========================
อาหารที่เลือกได้:
{", ".join(sample_foods)}

ร้านที่เลือกได้:
{", ".join(sample_shops)}
========================

user: {user_text}
"""


# ================== CALL GROQ ==================
def call_ai(text):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "ตอบ JSON เท่านั้น"},
            {"role": "user", "content": build_prompt(text)}
        ],
        "temperature": 0.2,
        "max_tokens": 150
    }

    try:
        res = requests.post(url, headers=headers, json=data)

        if res.status_code != 200:
            print("STATUS:", res.status_code)
            print("ERROR:", res.text)
            return {"type": "unknown"}

        content = res.json()["choices"][0]["message"]["content"].strip()

        # 🔥 แปลง JSON
        try:
            return json.loads(content)
        except:
            return {"type": "unknown"}

    except Exception as e:
        print("EXCEPTION:", e)
        return {"type": "unknown"}


# ================== TEST ==================
if __name__ == "__main__":
    while True:
        text = input("คุณ: ")
        result = call_ai(text)
        print("AI:", result)