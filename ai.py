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
    # แยกประเภทจาก JSON จริง
    food_types = list(foods.keys())

    # สุ่มอาหารต่อหมวด (ลด token)
    food_by_type = {}
    for t in food_types:
        items = [item["name"] for item in foods[t]]
        food_by_type[t] = random.sample(items, min(5, len(items)))

    sample_shops = random.sample(ALL_SHOPS, min(5, len(ALL_SHOPS)))

    # สร้าง text รายหมวด
    food_text = ""
    for t, items in food_by_type.items():
        food_text += f"{t}: {', '.join(items)}\n"

    return f"""
คุณคือ AI Chatbot สำหรับ "แนะนำอาหารและร้านอาหารเท่านั้น"

กฎสำคัญ:
- ห้ามตอบนอกเรื่องอาหาร
- ถ้าไม่เกี่ยว → ตอบ "ไม่เข้าใจคำถาม" เท่านั้น
- ห้ามอธิบายเพิ่ม
- ตอบสั้น

========================
logic
========================

1️ ถ้าเกี่ยวกับ "อยากกิน / หิว"
→ ให้เลือก "ประเภทอาหาร" 1 ประเภทก่อน แล้วแนะนำอาหาร 3 เมนูจากหมวดนั้น

2️ ถ้าเกี่ยวกับ "แนะนำเมนู"
→ ให้เลือก "ประเภทอาหาร" ที่เหมาะสม แล้วแนะนำ 3 เมนู

3️ ถ้า user ระบุประเภท เช่น:
- อยากกินเส้น → เมนูเส้น
- อยากกินของหวาน → ของหวาน
→ ให้เลือกประเภทนั้นโดยตรง

ประเภทที่มี:
{", ".join(food_types)}

4️ ถ้าเกี่ยวกับ "ร้านอาหาร"
→ แนะนำร้าน 3 ร้าน

5️ ถ้าไม่เกี่ยว
→ ไม่เข้าใจคำถาม

========================
 เมนู (ห้ามสร้างเอง ต้องเลือกจากนี้)
{food_text}

 ร้านอาหาร
{", ".join(sample_shops)}

========================
 รูปแบบคำตอบ

อาหาร:
ประเภท: <ชื่อประเภท>
แนะนำ: xxx, xxx, xxx

ร้าน:
แนะนำร้าน: xxx, xxx, xxx

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
