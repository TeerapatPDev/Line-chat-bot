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

    def build_prompt(user_text):
    return f"""
คุณคือ AI ที่ทำหน้าที่ "วิเคราะห์คำสั่ง" เท่านั้น (ไม่ใช่ chatbot)

กฎ:
- ห้ามตอบเป็นประโยค
- ห้ามอธิบาย
- ตอบเป็น format ที่กำหนดเท่านั้น

========================
TASK
========================

วิเคราะห์ข้อความผู้ใช้ แล้วเลือก 1 อย่าง:

1. ถ้าอยากกิน / หิว:
ตอบ → random_food

2. ถ้าต้องการเลือกประเภทอาหาร:
ตอบ → choose_type: [ชื่อประเภท]

ประเภทที่มี:
เมนูข้าว
เมนูเส้น
เมนูแกง
ของแซ่บ
ของหวาน
เครื่องดื่ม

3. ถ้าถามหาร้านอาหาร:
ตอบ → restaurant

4. ถ้าไม่เกี่ยว:
ตอบ → unknown

========================
ตัวอย่าง

user: หิวว่ะ
→ random_food

user: กินอะไรดี
→ random_food

user: อยากกินเส้น
→ choose_type: เมนูเส้น

user: ร้านไหนดี
→ restaurant

user: เล่นเกมไรดี
→ unknown

========================
user: {user_text}
"""


# ================== CALL GROQ ==================
def call_ai(text):
    url = "https://api.groq.com/openai/v1/chat/completions"

    system_prompt = "คุณคือ AI ที่ต้องทำตามกฎอย่างเคร่งครัด"

    user_prompt = build_prompt(text)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,   # ลดมั่ว
        "max_tokens": 200
    }

    try:
        res = requests.post(url, headers=headers, json=data)

        if res.status_code != 200:
            print("STATUS:", res.status_code)
            print("ERROR:", res.text)
            return "ไม่เข้าใจคำถาม"

        result = res.json()["choices"][0]["message"]["content"].strip()

        # กัน AI หลุด format
        if not result:
            return "ไม่เข้าใจคำถาม"

        return result

    except Exception as e:
        print("EXCEPTION:", e)
        return "ไม่เข้าใจคำถาม"


# ================== TEST ==================
if __name__ == "__main__":
    while True:
        text = input("คุณ: ")
        print("AI:", call_ai(text))
