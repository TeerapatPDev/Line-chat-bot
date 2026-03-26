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

# ================== FLEX ==================
def build_random_3_foods():
    all_foods = []
    for f in foods.values():
        all_foods.extend(f)

    random_foods = random.sample(all_foods, min(3, len(all_foods)))

    bubbles = []
    for food in random_foods:
        bubbles.append({
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
        })

    return {
        "type": "flex",
        "altText": "สุ่มอาหาร",
        "contents": {"type": "carousel", "contents": bubbles}
    }


def build_food_list(type_name):
    food_list = foods.get(type_name, [])
    if not food_list:
        return {"type": "text", "text": "ฉันไม่เข้าใจ"}

    random_foods = random.sample(food_list, min(3, len(food_list)))

    bubbles = []
    for food in random_foods:
        bubbles.append({
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
        })

    return {
        "type": "flex",
        "altText": f"{type_name}",
        "contents": {"type": "carousel", "contents": bubbles}
    }


def build_shop_flex():
    bubbles = []
    for s in shop.values():
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


# ================== QUICK REPLY ==================
def add_quick_reply(message):
    message["quickReply"] = {
        "items": [
            {"type": "action", "action": {"type": "message", "label": "🍛 สุ่มอาหาร", "text": "สุ่มอาหาร"}},
            {"type": "action", "action": {"type": "message", "label": "🤔 กินอะไรดี", "text": "กินอะไรดี"}},
            {"type": "action", "action": {"type": "message", "label": "📍 ร้าน", "text": "แนะนำร้านอาหาร"}}
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

    if "events" not in body or len(body["events"]) == 0:
        return {"status": "ok"}

    event = body["events"][0]
    reply_token = event.get("replyToken")

    if not reply_token:
        return {"status": "ok"}

    if event.get("type") == "follow":
        reply(reply_token, add_quick_reply({
            "type": "text",
            "text": "ยินดีต้อนรับ 😄"
        }))
        return {"status": "ok"}

    if event.get("type") != "message":
        return {"status": "ok"}

    if event["message"].get("type") != "text":
        reply(reply_token, {"type": "text", "text": "ฉันไม่เข้าใจ"})
        return {"status": "ok"}

    text = event["message"].get("text", "").strip()

    if not text:
        reply(reply_token, {"type": "text", "text": "ฉันไม่เข้าใจ"})
        return {"status": "ok"}

    # ================== AI ==================
    ai_result = call_ai(text).lower().strip()
    print("USER:", text)
    print("AI:", ai_result)

    valid_types = ["เมนูข้าว","เมนูเส้น","เมนูแกง","ของแซ่บ","ของหวาน","เครื่องดื่ม"]

    # ================== ROUTE ==================
    if "random_food" in ai_result:
        message = build_random_3_foods()

    elif "choose_type" in ai_result:
        try:
            type_name = ai_result.split(":")[1].strip()
            if type_name in valid_types:
                message = build_food_list(type_name)
            else:
                message = {"type": "text", "text": "ฉันไม่เข้าใจ"}
        except:
            message = {"type": "text", "text": "ฉันไม่เข้าใจ"}

    elif "restaurant" in ai_result:
        message = build_shop_flex()

    else:
        message = {"type": "text", "text": "ฉันไม่เข้าใจ"}

    reply(reply_token, add_quick_reply(message))
    return {"status": "ok"}