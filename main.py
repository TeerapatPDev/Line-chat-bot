from fastapi import FastAPI, Request
import requests
import random
import json
import re

app = FastAPI()

LINE_TOKEN = "qV+t4FvU+6T0ZGeVi6/jLenoS+sPd/6OAm0dyl+GPd10nktsD2WXXlY7qtFwGSVH57+hZd17yXHtUBonfDFkc+5Db/0YgSIWnbon3BpgbCjrFhTRIeBNf3u6jA6apVVzJh17TyPvB72VXrEW272RIAdB04t89/1O/w1cDnyilFU="

# ================== LOAD DATA ==================
with open("data/foods.json", "r", encoding="utf-8") as f:
    foods = json.load(f)

with open("data/shops.json", "r", encoding="utf-8") as f:
    shop = json.load(f)

# ================== INTENT ==================
def detect_intent(text):
    text = text.strip()

    # 🔥 เลือก type (สำคัญต้องอยู่บนสุด)
    if text in foods.keys():
        return "choose_type"

    # ร้านอาหาร
    if re.search(r"(ร้าน|ของกิน|อาหาร).*(ไหนดี|แนะนำ|อร่อย|เด็ด|บ้าง)", text) \
       or re.search(r"(แนะนำ|มี).*(ร้าน|ของกิน|อาหาร)", text):
        return "recommend_restaurant"

    # กินอะไรดี
    elif re.search(r"(กิน|ทาน|แดก).*(อะไร|ไร).*ดี|มีอะไรน่ากิน", text):
        return "recommend_food"

    # หิว
    elif re.search(r"(หิว|อยากกิน|โคตรหิว)", text):
        if re.search(r"ไม่หิว", text):
            return "not_hungry"
        return "hungry"

    return "unknown"

# ================== FLEX ==================
def build_food_flex(food):
    return {
        "type": "flex",
        "altText": "food suggestion",
        "contents": {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": food["image"],
                "size": "full"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": food["name"], "weight": "bold", "size": "xl"},
                    {"type": "text", "text": f"พลังงาน: {food['nutrition']}"},
                    {"type": "text", "text": f"โปรตีน: {food['protein']}"}
                ]
            }
        }
    }

def build_random_3_foods():
    all_foods = []

    for food_list in foods.values():
        all_foods.extend(food_list)

    random_foods = random.sample(all_foods, min(3, len(all_foods)))

    bubbles = []

    for food in random_foods:
        bubbles.append({
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": food["image"],
                "size": "full"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": food["name"], "weight": "bold"},
                    {"type": "text", "text": f"🔥 {food['nutrition']}"},
                    {"type": "text", "text": f"💪 {food['protein']}"}
                ]
            }
        })

    return {
        "type": "flex",
        "altText": "สุ่มอาหาร",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }

# 🔥 เลือกประเภทอาหาร
def build_type_flex():
    buttons = []

    for food_type in foods.keys():
        buttons.append({
            "type": "button",
            "style": "primary",
            "margin": "sm",
            "action": {
                "type": "message",
                "label": food_type,
                "text": food_type
            }
        })

    return {
        "type": "flex",
        "altText": "เลือกประเภทอาหาร",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🍽️ เลือกประเภทอาหาร",
                        "weight": "bold",
                        "size": "xl"
                    }
                ]
            },
            "footer": {   # 🔥 ใส่ปุ่มตรงนี้!
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": buttons
            }
        }
    }

# 🔥 รายการอาหารใน type
def build_food_list(type_name):
    food_list = foods[type_name]

    # 🔥 สุ่ม 4 เมนู
    random_foods = random.sample(food_list, min(4, len(food_list)))

    bubbles = []

    for food in random_foods:
        bubbles.append({
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": food["image"],
                "size": "full",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": food["name"],
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": f"🔥 {food['nutrition']}",
                        "size": "sm",
                        "color": "#888888"
                    },
                    {
                        "type": "text",
                        "text": f"💪 โปรตีน {food['protein']}",
                        "size": "sm",
                        "color": "#888888"
                    }
                ]
            }
        })

    return {
        "type": "flex",
        "altText": f"เมนู {type_name}",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }

def build_shop_flex():
    bubbles = []

    for s in shop.values():
        bubbles.append({
            "type": "bubble",
            "hero": {   # 🔥 ใส่รูปตรงนี้
                "type": "image",
                "url": s["image"],
                "size": "full",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": s["name"],
                        "weight": "bold",
                        "size": "lg"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "📍 เปิดแผนที่",
                            "uri": s["location"]
                        }
                    }
                ]
            }
        })

    return {
        "type": "flex",
        "altText": "ร้านอาหารแนะนำ",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }

# ================== QUICK REPLY ==================
def add_quick_reply(message):
    message["quickReply"] = {
        "items": [
            {
                "type": "action",
                "action": {"type": "message", "label": "🍛 สุ่มอาหาร", "text": "สุ่มอาหาร"}
            },
            {
                "type": "action",
                "action": {"type": "message", "label": "🤔 กินอะไรดี", "text": "กินอะไรดี"}
            },
            {
                "type": "action",
                "action": {"type": "message", "label": "📍 ร้าน", "text": "แนะนำร้านอาหาร"}
            }
        ]
    }
    return message

# ================== REPLY ==================
def reply(reply_token, message):
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Authorization": f"Bearer {LINE_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "replyToken": reply_token,
            "messages": [message]
        }
    )

# ================== WEBHOOK ==================
@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()
    event = body["events"][0]
    reply_token = event["replyToken"]

    # 🟢 FOLLOW (add bot)
    if event["type"] == "follow":
        message = add_quick_reply({
            "type": "text",
            "text": "ยินดีต้อนรับครับ 😄\nอยากกินอะไรพิมพ์มาได้เลย!"
        })
        reply(reply_token, message)
        return {"status": "ok"}

    # ❗ ignore event อื่น
    if event["type"] != "message":
        return {"status": "ok"}

    msg = event["message"]

    if msg["type"] != "text":
        return {"status": "ok"}

    text = msg["text"].strip()

    # 🔥 detect intent
    intent = detect_intent(text)
    print(f"text: {text} → intent: {intent}")

    # ================== LOGIC ==================
    if intent == "recommend_food":
        message = build_type_flex()

    elif intent == "choose_type":
        message = build_food_list(text)

    elif text == "สุ่มอาหาร":
        message = build_random_3_foods()

    elif intent == "hungry":
        t = random.choice(list(foods.keys()))
        food = random.choice(foods[t])
        message = build_food_flex(food)

    elif intent == "recommend_restaurant":
        message = build_shop_flex()

    elif intent == "not_hungry":
        message = {"type": "text", "text": "อ้าว ไม่หิวแล้วหรอ 😅"}

    else:
        message = {"type": "text", "text": "ลองเลือกเมนูดูนะ 😄"}

    # ✅ ใส่ quick reply ทุกครั้ง
    message = add_quick_reply(message)

    # 🔥 reply
    reply(reply_token, message)

    return {"status": "ok"}