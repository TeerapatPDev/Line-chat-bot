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
    # สุ่มอาหาร/ร้านมาใส่ใน prompt เพื่อลด token
    sample_foods = random.sample(ALL_FOODS, min(15, len(ALL_FOODS)))
    sample_shops = random.sample(ALL_SHOPS, min(5, len(ALL_SHOPS)))

    return f"""
คุณคือ AI Chatbot สำหรับ "แนะนำอาหารและร้านอาหารเท่านั้น"

กฎสำคัญ:
- ห้ามตอบนอกเรื่องอาหาร
- ถ้าไม่เกี่ยว → ตอบ "ไม่เข้าใจคำถาม" เท่านั้น
- ห้ามอธิบายเพิ่ม
- ตอบสั้น

========================
 logic (ตรวจจับ intent)
========================

1️ ถ้าเกี่ยวกับ "อยากกิน / หิว"
ตัวอย่าง keyword:
- หิว, หิวแล้ว, หิวมาก, หิวจัด, โคตรหิว, หิววว
- อยากกิน, อยากแดก, อยากทาน
- หาอะไรกิน, มีอะไรกิน
- กินไรดี, กินอะไรดี, แดกไรดี
- หาของกิน, ของกินมีอะไร
 ให้แนะนำ "อาหาร 2 อย่าง"

------------------------

2️ ถ้าเกี่ยวกับ "แนะนำเมนู"
ตัวอย่าง keyword:
- แนะนำอาหาร, แนะนำเมนู
- มีเมนูอะไรบ้าง
- เมนูน่ากิน, เมนูยอดฮิต
 ให้แนะนำ "อาหาร 2 อย่าง"

------------------------

3️ ถ้าเกี่ยวกับ "ร้านอาหาร"
ตัวอย่าง keyword:
- ร้านอาหาร, ร้านข้าว, ร้านกินข้าว
- ร้านไหนดี, ไปกินร้านไหนดี
- มีร้านแนะนำไหม
- ร้านเด็ด, ร้านอร่อย
- ของกินแถวนี้, ร้านใกล้ฉัน
 ให้แนะนำ "ร้าน 2 ร้าน"

------------------------

4️ ถ้าไม่เกี่ยวกับอาหารเลย
ตัวอย่าง:
- เล่นเกมอะไรดี
- ซักผ้ายัง
- ทำการบ้านยัง
 ตอบ: ไม่เข้าใจคำถาม

========================
 เมนู (เลือกได้เท่านั้น)
{", ".join(sample_foods)}

 ร้านอาหาร
{", ".join(sample_shops)}

========================
 รูปแบบคำตอบ

อาหาร:
แนะนำ: xxx, xxx

ร้าน:
แนะนำร้าน: xxx, xxx

อื่น:
ไม่เข้าใจคำถาม

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
