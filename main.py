from fastapi import FastAPI, Request
import requests
import random
import json
import re

app = FastAPI()

LINE_TOKEN = "+pIb40AfdSa2H+vIWscb871CSr4NWUmYPapSVLlYiPo7YcAia5OBDjrpmDzxmz9FQUKWCWkCf2hejHTjx8N1zacNmsPsGp50o5JqP+ce+5fMl2y9i0DxdFnNMStTjaRlw6OZPlqnFXWLayC3ls2D+gdB04t89/1O/w1cDnyilFU="

# ================== LOAD DATA ==================
with open("data/foods.json", "r", encoding="utf-8") as f:
    foods = json.load(f)

with open("data/shops.json", "r", encoding="utf-8") as f:
    shop = json.load(f)

# ================== INTENT ==================
def detect_intent(text):
    # 🟢 ร้านอาหาร (ครอบคลุมคำใกล้เคียง)
    if re.search(r"(ร้าน|ของกิน|อาหาร).*(ไหนดี|แนะนำ|อร่อย|เด็ด|บ้าง)", text) \
       or re.search(r"(แนะนำ|มี).*(ร้าน|ของกิน|อาหาร)", text):
        return "recommend_restaurant"

    # 🟡 กินอะไรดี
    elif re.search(r"(กิน|ทาน|แดก).*(อะไร|ไร).*ดี|มีอะไรน่ากิน", text):
        return "recommend_food"

    # 🔴 หิว
    elif re.search(r"(หิว|อยากกิน|โคตรหิว)", text):
        if re.search(r"ไม่หิว", text):
            return "not_hungry"
        return "hungry"

    return "unknown"

# ================== BUILD MESSAGE ==================
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

def build_shop_flex():
    bubbles = []

    for s in shop.values():
        bubbles.append({
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": s["name"], "weight": "bold", "size": "xl"}
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
                            "label": "เปิด Google Maps",
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

# ================== WEBHOOK ==================
@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()
    event = body["events"][0]
    reply_token = event["replyToken"]

    # default message
    message = {"type": "text", "text": "ฉันไม่เข้าใจ"}

    if event["type"] == "message":
        msg = event["message"]

        if msg["type"] == "text":
            text = msg["text"]

            # 🔥 detect intent ตรงนี้
            intent = detect_intent(text)

            print(f"text: {text} → intent: {intent}")  # debug

            if intent in ["hungry", "recommend_food"]:
                food = random.choice(list(foods.values()))
                message = build_food_flex(food)

            elif intent == "recommend_restaurant":
                message = build_shop_flex()

            elif intent == "not_hungry":
                message = {"type": "text", "text": "อ้าว ไม่หิวแล้วหรอ 😅"}

    # ================== REPLY ==================
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

    return {"status": "ok"}