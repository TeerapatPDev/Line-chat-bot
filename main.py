from fastapi import FastAPI, Request
import requests
import random
import json
import os

from dotenv import load_dotenv
from ai import call_ai

app = FastAPI()

# ================== LOAD ENV ==================
load_dotenv()
LINE_TOKEN = os.getenv("LINE_TOKEN")

# ================== LOAD DATA ==================
with open("data/foods.json", "r", encoding="utf-8") as f:
    foods = json.load(f)

with open("data/shops.json", "r", encoding="utf-8") as f:
    shop = json.load(f)

# ================== HELPERS ==================
def find_food_object(name):
    for category_foods in foods.values():
        for food in category_foods:
            if food["name"] == name:
                return food
    return None


def find_food_objects_by_category(category, count=3):
    if category in foods:
        pool = foods[category]
    else:
        pool = [f for cat in foods.values() for f in cat]
    return random.sample(pool, min(count, len(pool)))


# ================== FLEX ==================
def build_food_bubble(food):
    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": food["image"],
            "size": "full",
            "aspectMode": "cover",
            "aspectRatio": "16:9"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": food["name"], "weight": "bold", "size": "md"},
                {"type": "text", "text": f"พลังงาน: {food['nutrition']}"},
                {"type": "text", "text": f"โปรตีน: {food['protein']}"}
            ]
        }
    }


def build_food_carousel(food_objects, alt_text="แนะนำอาหาร"):
    bubbles = [build_food_bubble(f) for f in food_objects]
    return {
        "type": "flex",
        "altText": alt_text,
        "contents": {"type": "carousel", "contents": bubbles}
    }


def build_shop_flex(shop_objects):
    bubbles = []
    for s in shop_objects:
        bubbles.append({
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": s["image"],
                "size": "full",
                "aspectMode": "cover",
                "aspectRatio": "16:9"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": s["name"], "weight": "bold", "size": "lg"}
                ]
            },
            "footer": {
                "type": "box",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "เปิดแผนที่",
                            "uri": s["location"]
                        }
                    }
                ]
            }
        })

    return {
        "type": "flex",
        "altText": "ร้านอาหาร",
        "contents": {"type": "carousel", "contents": bubbles}
    }


# ================== BUILD FROM AI ==================
def build_from_ai(ai_result):
    result_type = ai_result.get("type")
    message_text = ai_result.get("message", "ลองดูตัวเลือกนี้นะ!")

    # ❗ unknown หรือ error
    if result_type not in ("food", "shop"):
        return [{"type": "text", "text": "ไม่เข้าใจคำถาม"}]

    # ================= FOOD =================
    if result_type == "food":
        item_names = ai_result.get("items", [])
        category = ai_result.get("category", "mixed")

        food_objects = []
        for name in item_names:
            obj = find_food_object(name)
            if obj:
                food_objects.append(obj)

        # fallback
        if not food_objects:
            food_objects = find_food_objects_by_category(category, 3)

        if len(food_objects) < 3:
            extra = find_food_objects_by_category(category, 3 - len(food_objects))
            food_objects.extend(extra)

        flex = build_food_carousel(food_objects[:3], f"เมนู{category}")

        return [
            {"type": "text", "text": message_text},
            flex
        ]

    # ================= SHOP =================
    if result_type == "shop":
        item_names = ai_result.get("items", [])

        shop_objects = [s for s in shop.values() if s["name"] in item_names]

        if not shop_objects:
            shop_objects = list(shop.values())

        flex = build_shop_flex(shop_objects[:3])

        return [
            {"type": "text", "text": message_text},
            flex
        ]


# ================== REPLY ==================
def reply(reply_token, messages):
    if not isinstance(messages, list):
        messages = [messages]

    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Authorization": f"Bearer {LINE_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "replyToken": reply_token,
            "messages": messages
        }
    )


# ================== WEBHOOK ==================
@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()

    if "events" not in body or len(body["events"]) == 0:
        return {"status": "ok"}

    event = body["events"][0]
    reply_token = event.get("replyToken")

    if not reply_token:
        return {"status": "ok"}

    # follow
    if event.get("type") == "follow":
        reply(reply_token, {"type": "text", "text": "ยินดีต้อนรับ 😄"})
        return {"status": "ok"}

    # message
    if event.get("type") != "message":
        return {"status": "ok"}

    if event["message"].get("type") != "text":
        reply(reply_token, {"type": "text", "text": "ไม่เข้าใจคำถาม"})
        return {"status": "ok"}

    text = event["message"].get("text", "").strip()

    if not text:
        reply(reply_token, {"type": "text", "text": "ไม่เข้าใจคำถาม"})
        return {"status": "ok"}

    # ================= AI ONLY =================
    ai_result = call_ai(text)
    print("USER:", text)
    print("AI:", ai_result)

    messages = build_from_ai(ai_result)

    reply(reply_token, messages)
    return {"status": "ok"}