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
def get_foods_by_category():
    """คืน dict ของแต่ละหมวด → รายชื่ออาหาร"""
    return {cat: [item["name"] for item in items] for cat, items in foods.items()}


def get_all_shops():
    return [s["name"] for s in shops.values()]


FOODS_BY_CAT = get_foods_by_category()
ALL_SHOPS = get_all_shops()

# สุ่มตัวอย่างแต่ละหมวด สำหรับใส่ใน prompt
def sample_foods_text():
    lines = []
    for cat, names in FOODS_BY_CAT.items():
        sample = random.sample(names, min(4, len(names)))
        lines.append(f"  {cat}: {', '.join(sample)}")
    return "\n".join(lines)


# ================== BUILD PROMPT ==================
def build_prompt(user_text):
    sample_shops = random.sample(ALL_SHOPS, min(3, len(ALL_SHOPS)))
    foods_text = sample_foods_text()

    return f"""
คุณคือ AI แนะนำอาหารและร้านอาหาร ตอบเป็น JSON เท่านั้น ห้ามมี text อื่นนอกจาก JSON

=== หมวดอาหารที่มี ===
{foods_text}

=== ร้านอาหารที่มี ===
  {', '.join(sample_shops)}

=== กฎการตอบ ===
1. วิเคราะห์ว่าผู้ใช้ถามเกี่ยวกับหมวดไหน หรือถามทั่วไป
2. ถ้าถามเกี่ยวกับ "ร้านอาหาร" → type = "shop"
3. ถ้าถามเกี่ยวกับอาหารทั่วไป / หิว / สุ่ม → type = "food" แนะนำจากหลายหมวด
4. ถ้าระบุหมวดชัดเจน เช่น "อยากกินของแซ่บ" → type = "food" เลือกจากหมวดนั้น
5. ถ้าไม่เกี่ยวกับอาหารเลย → type = "unknown"
6. แนะนำ 3 รายการเสมอ (ยกเว้น unknown)
7. ต้องมี field "message" เสมอ
8. message ต้องเป็นประโยคธรรมชาติ เหมือนคุยกับเพื่อน
9. ห้ามยาวเกิน 1 ประโยค

=== รูปแบบ JSON ที่ต้องตอบ ===

กรณีแนะนำอาหาร:
{{
  "type": "food",
  "message": "ข้อความคุยกับผู้ใช้ เช่น หิวแล้วใช่ไหม ลองนี่เลย!",
  "category": "ชื่อหมวด หรือ mixed ถ้าหลายหมวด",
  "items": ["ชื่ออาหาร1", "ชื่ออาหาร2", "ชื่ออาหาร3"]
}}

กรณีแนะนำร้าน:
{{
  "type": "shop",
  "message": "ข้อความแนะนำร้าน เช่น ลองร้านพวกนี้ดูนะ!",
  "items": ["ชื่อร้าน1", "ชื่อร้าน2", "ชื่อร้าน3"]
}}

กรณีไม่เกี่ยว:
{{
  "type": "unknown",
  "message": "ไม่เข้าใจคำถาม"
}}

=== ตัวอย่าง ===
user: "หิวแล้ว" → {{"type":"food","category":"mixed","items":["ข้าวผัด","ก๋วยเตี๋ยว","ส้มตำ"]}}
user: "อยากกินของหวาน" → {{"type":"food","category":"ของหวาน","items":["ข้าวเหนียวมะม่วง","บัวลอย","ลอดช่อง"]}}
user: "อยากกินของแซ่บๆ" → {{"type":"food","category":"ของแซ่บ","items":["ส้มตำ","ลาบหมู","ต้มแซ่บกระดูกอ่อน"]}}
user: "มีเมนูเส้นอะไรบ้าง" → {{"type":"food","category":"เมนูเส้น","items":["ผัดไทย","ก๋วยเตี๋ยวเรือ","บะหมี่หมูแดง"]}}
user: "แนะนำร้านอาหาร" → {{"type":"shop","items":["ร้านข้าวฟางคาเฟ่","กิ๋นนี่เน้อ","Term Waan cafe"]}}
user: "เล่นเกมอะไรดี" → {{"type":"unknown"}}

=== คำถามของผู้ใช้ ===
user: {user_text}
"""


# ================== CALL GROQ ==================
def call_ai(text) -> dict:
    """
    คืน dict เสมอ:
      {"type": "food", "category": "...", "items": [...]}
      {"type": "shop", "items": [...]}
      {"type": "unknown"}
      {"type": "error"}   ← กรณี API ล้มเหลว
    """
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "คุณคือ AI แนะนำอาหาร ตอบเป็น JSON เท่านั้น ห้ามมี text อื่น ห้ามมี markdown backtick"
            },
            {
                "role": "user",
                "content": build_prompt(text)
            }
        ],
        "temperature": 0.2,
        "max_tokens": 200
    }

    try:
        res = requests.post(url, headers=headers, json=data)

        if res.status_code != 200:
            print("STATUS:", res.status_code)
            print("ERROR:", res.text)
            return {"type": "error"}

        raw = res.json()["choices"][0]["message"]["content"].strip()

        # ลบ markdown backtick กัน AI แอบใส่
        raw = raw.replace("```json", "").replace("```", "").strip()

        result = json.loads(raw)

        # validate type
        if result.get("type") not in ("food", "shop", "unknown"):
            return {"type": "unknown"}

        return result

    except json.JSONDecodeError as e:
        print("JSON PARSE ERROR:", e)
        print("RAW:", raw)
        return {"type": "error"}

    except Exception as e:
        print("EXCEPTION:", e)
        return {"type": "error"}


# ================== TEST ==================
if __name__ == "__main__":
    while True:
        text = input("คุณ: ")
        result = call_ai(text)
        print("AI JSON:", json.dumps(result, ensure_ascii=False, indent=2))