from difflib import get_close_matches
import os
from fastapi import FastAPI, Request
import requests
import random
import json
from dotenv import load_dotenv
import logging

from ai import call_ai

app = FastAPI()

# ================== LOGGING ==================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ================== ENV ==================
load_dotenv()
LINE_TOKEN = os.getenv("LINE_TOKEN")

# ================== LOAD DATA ==================
with open("data/foods.json", "r", encoding="utf-8") as f:
    foods = json.load(f)

with open("data/shops.json", "r", encoding="utf-8") as f:
    shop = json.load(f)

# ================== HELPER ==================
def get_all_foods():
    all_foods = []
    for f in foods.values():
        all_foods.extend(f)
    return all_foods

def get_foods_by_names(names):
    all_foods = get_all_foods()
    result = []
    for name in names:
        for food in all_foods:
            if food["name"] == name:
                result.append(food)
    return result

# ================== NORMALIZE ==================
def normalize_foods(food_data):
    all_foods = get_all_foods()
    # เติมให้ครบ 3 ถ้าน้อย
    if len(food_data) < 3:
        existing = [f["name"] for f in food_data]
        remaining = [f for f in all_foods if f["name"] not in existing]
        if remaining:
            extra = random.sample(remaining, min(3 - len(food_data), len(remaining)))
            food_data.extend(extra)
    # ตัดให้เหลือ 3 ถ้าเกิน
    if len(food_data) > 3:
        food_data = food_data[:3]
    return food_data

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
                    {"type": "text", "text": food["name"], "weight": "bold", "wrap": True},
                    {"type": "text", "text": f"พลังงาน: {food['nutrition']}"},
                    {"type": "text", "text": f"โปรตีน: {food['protein']}"}
                ]
            }
        })
    flex = {
        "type": "flex",
        "altText": "AI แนะนำอาหาร",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }
    logging.info(f"Built food flex message: {flex}")
    return flex

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
                    {"type": "text", "text": s["name"], "weight": "bold", "wrap": True}
                ]
            },
            "footer": {
                "type": "button",
                "action": {"type": "uri", "label": "เปิดแผนที่", "uri": s["location"]}
            }
        })
    flex = {
        "type": "flex",
        "altText": "ร้านอาหาร",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }
    logging.info(f"Built shop flex message: {flex}")
    return flex

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
def reply(reply_token, message, pre_text=None):
    messages = []
    if pre_text:
        messages.append({"type": "text", "text": pre_text})
    messages.append(message)
    logging.info(f"Sending reply: {messages}")
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
        reply(reply_token, add_quick_reply({"type": "text", "text": "ยินดีต้อนรับ 😄"}))
        return {"status": "ok"}

    # ไม่ใช่ message
    if event.get("type") != "message":
        return {"status": "ok"}

    if event["message"].get("type") != "text":
        reply(reply_token, add_quick_reply({"type": "text", "text": "ฉันไม่เข้าใจ"}))
        return {"status": "ok"}

    text = event["message"].get("text", "").strip()
    if not text:
        reply(reply_token, add_quick_reply({"type": "text", "text": "ฉันไม่เข้าใจ"}))
        return {"status": "ok"}

    # ================== AI ONLY ==================
    ai_result = call_ai(text)
    logging.info(f"AI result: {ai_result}")

    # ใช้ข้อความนำจาก AI ถ้ามี
    pre_text = ai_result.get("intro_text", None)

    # 🔥 food
    if ai_result.get("type") == "food":
        food_data = get_foods_by_names(ai_result.get("items", []))
        if food_data:
            food_data = normalize_foods(food_data)  # ⭐ บังคับ 3 เมนู
            message = build_ai_food_flex(food_data)
            reply(reply_token, add_quick_reply(message), pre_text=pre_text)
            return {"status": "ok"}

    # 🔥 shop
    elif ai_result.get("type") == "shop":
        message = build_shop_flex()
        reply(reply_token, add_quick_reply(message), pre_text=pre_text)
        return {"status": "ok"}