import os
from fastapi import FastAPI, Request
import requests
import random
import json
from dotenv import load_dotenv
import logging

from ai import call_ai

app = FastAPI()

# ================== LOG ==================
logging.basicConfig(level=logging.INFO)

# ================== ENV ==================
load_dotenv()
LINE_TOKEN = os.getenv("LINE_TOKEN")

# ================== LOAD DATA ==================
with open("data/foods.json", "r", encoding="utf-8") as f:
    foods = json.load(f)

with open("data/shops.json", "r", encoding="utf-8") as f:
    shops = json.load(f)

# ================== HELPER ==================
def get_all_foods():
    all_foods = []
    for f in foods.values():
        all_foods.extend(f)
    return all_foods

def get_foods_by_names(names):
    return [f for f in get_all_foods() if f["name"] in names]

def get_shops_by_names(names):
    return [s for s in shops.values() if s["name"] in names]

# ================== NORMALIZE ==================
def normalize_foods(food_data):
    all_foods = get_all_foods()

    if len(food_data) < 3:
        existing = [f["name"] for f in food_data]
        remaining = [f for f in all_foods if f["name"] not in existing]

        if remaining:
            food_data += random.sample(remaining, min(3 - len(food_data), len(remaining)))

    return food_data[:3]

# ================== FLEX ==================
def build_ai_food_flex(food_list):
    bubbles = []

    for food in food_list:
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
                    {"type": "text", "text": food["name"], "weight": "bold"},
                    {"type": "text", "text": f"พลังงาน: {food['nutrition']}"},
                    {"type": "text", "text": f"โปรตีน: {food['protein']}"}
                ]
            }
        })

    return {
        "type": "flex",
        "altText": "AI แนะนำอาหาร",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }


def build_shop_flex(shop_list):
    bubbles = []

    for s in shop_list:
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
                    {"type": "text", "text": s["name"], "weight": "bold"}
                ]
            },
            "footer": {
                "type": "button",
                "action": {
                    "type": "uri",
                    "label": "เปิดแผนที่",
                    "uri": s["location"]
                }
            }
        })

    return {
        "type": "flex",
        "altText": "ร้านอาหาร",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
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
def reply(reply_token, messages):
    logging.info(messages)

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

    if "events" not in body:
        return {"status": "ok"}

    event = body["events"][0]
    reply_token = event.get("replyToken")

    if not reply_token:
        return {"status": "ok"}

    # follow
    if event.get("type") == "follow":
        reply(reply_token, [{"type": "text", "text": "ยินดีต้อนรับ 😄"}])
        return {"status": "ok"}

    if event.get("type") != "message":
        return {"status": "ok"}

    text = event["message"].get("text", "").strip()

    if not text:
        reply(reply_token, [{"type": "text", "text": "ฉันไม่เข้าใจ"}])
        return {"status": "ok"}

    # ================== AI ==================
    ai_result = call_ai(text)
    logging.info(f"AI result: {ai_result}")

    messages = []

    # intro text
    if ai_result.get("intro_text"):
        messages.append({"type": "text", "text": ai_result["intro_text"]})

    # FOOD
    if ai_result.get("type") == "food":
        food_data = get_foods_by_names(ai_result.get("items", []))
        food_data = normalize_foods(food_data)

        if food_data:
            messages.append(add_quick_reply(build_ai_food_flex(food_data)))
            reply(reply_token, messages)
            return {"status": "ok"}

    # SHOP
    if ai_result.get("type") == "shop":
        shop_data = get_shops_by_names(ai_result.get("items", []))

        if not shop_data:
            shop_data = list(shops.values())[:3]

        messages.append(add_quick_reply(build_shop_flex(shop_data)))
        reply(reply_token, messages)
        return {"status": "ok"}

    # fallback
    reply(reply_token, [{"type": "text", "text": "ฉันไม่เข้าใจ"}])
    return {"status": "ok"}