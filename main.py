from difflib import get_close_matches

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

# ================== NLP ==================
def simple_tokenize(text):
    tokens = re.split(r'\s+', text)
    if len(tokens) == 1:
        tokens = list(text)
    return tokens

def is_similar(word, keywords, cutoff=0.6):
    return len(get_close_matches(word, keywords, n=1, cutoff=cutoff)) > 0


# ================== DETECT INTENT ==================
def detect_intent(text):
    if not text:
        return "unknown"

    # lowercase + strip space
    text = text.lower().strip()

    # normalize slang
    text = text.replace("แดก", "กิน")
    text = text.replace("ไร", "อะไร")

    # ลบ emoji / symbol ยกเว้นตัวอักษรไทย-อังกฤษ-ตัวเลข
    text_clean = re.sub(r'[^\w\sก-๙]', '', text)

    # =========================
    # 1️⃣ RANDOM FOOD (สุ่มอาหาร)
    # =========================
    # เช็คคำ "สุ่ม" หรือ "สุ่มอาหาร" ครอบคลุมทุกกรณี
    if re.search(r"(สุ่ม)", text_clean):
        return "random_food"

    # =========================
    # 2️⃣ เลือกประเภท exact
    # =========================
    if text_clean in foods.keys():
        return "choose_type"

    # =========================
    # 3️⃣ ร้านอาหาร
    # =========================
    if re.search(r"(ร้าน|ของกิน|อาหาร).*(แนะนำ|อร่อย|เด็ด|ไหนดี|บ้าง|หน่อย)?", text_clean) \
       or re.search(r"(แนะนำ|มี|มีร้าน).*?(ร้าน|อาหาร|ของกิน)", text_clean):
        return "recommend_restaurant"

    # =========================
    # 4️⃣ กินอะไรดี / แนะนำเมนู
    # =========================
    if re.search(r"(กิน|ทาน).*(อะไร|เมนู|อะไรดี|มีอะไรน่ากิน|จะกินอะไร).*", text_clean):
        return "recommend_food"

    # =========================
    # 5️⃣ หิว / อยากกิน
    # =========================
    if re.search(r"(หิว|อยากกิน|โคตรหิว|หิวมาก|หิววว)+", text_clean):
        if re.search(r"(ไม่หิว|อิ่มแล้ว|อิ่ม)", text_clean):
            return "not_hungry"
        return "hungry"
    if re.search(r"(ไม่หิว|อิ่มแล้ว|อิ่ม)", text_clean):
        return "not_hungry"

    # =========================
    # 6️⃣ Fuzzy match type
    # =========================
    for key in foods.keys():
        if is_similar(text_clean, [key]):
            return "choose_type"

    # =========================
    # 7️⃣ NLP fallback
    # =========================
    tokens = simple_tokenize(text_clean)
    score = {"recommend_food":0, "recommend_restaurant":0, "hungry":0}
    food_words = ["กิน","อาหาร","ของกิน","เมนู"]
    recommend_words = ["แนะนำ","อะไร","ไหนดี","บ้าง","หน่อย"]
    restaurant_words = ["ร้าน","ร้านอาหาร"]
    hungry_words = ["หิว","อยากกิน"]

    for token in tokens:
        if is_similar(token, food_words): score["recommend_food"]+=1
        if is_similar(token, recommend_words): score["recommend_food"]+=1
        if is_similar(token, restaurant_words): score["recommend_restaurant"]+=2
        if is_similar(token, hungry_words): score["hungry"]+=2

    best = max(score, key=score.get)
    return best if score[best]>0 else "unknown"

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
                "size": "full",
                "aspectMode": "cover",   # บีบเต็ม
                "aspectRatio": "16:9"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": food["name"], "weight": "bold", "size": "lg", "wrap": True},
                    {"type": "text", "text": f"พลังงาน: {food['nutrition']}"},
                    {"type": "text", "text": f"โปรตีน: {food['protein']}"}
                ]
            }
        }
    }
# 🔥 สุ่มจากทั้งหมด 3 เมนู
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
                "aspectMode": "cover",   # บีบเต็ม
                "aspectRatio": "16:9"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": food["name"], "weight": "bold", "size": "md", "wrap": True},
                    {"type": "text", "text": f"พลังงาน: {food['nutrition']}"},
                    {"type": "text", "text": f"โปรตีน: {food['protein']}"}
                ]
            }
        })


    return {"type": "flex", "altText": "สุ่มอาหาร", "contents": {"type": "carousel", "contents": bubbles}}

# 🔥 เลือกประเภท
def build_type_flex():
    buttons = []
    for t in foods.keys():
        buttons.append({
            "type": "button",
            "style": "primary",
            "color": "#00AA00",  # สีเขียว
            "action": {"type": "message", "label": t, "text": t}
        })

    # แต่ละปุ่มอยู่แถวเดียว
    button_rows = []
    for btn in buttons:
        row = {"type": "box", "layout": "vertical", "spacing": "sm", "contents": [btn]}
        button_rows.append(row)

    return {
        "type": "flex",
        "altText": "เลือกประเภทอาหาร",
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": "เลือกประเภทอาหาร", "weight": "bold", "size": "lg", "align": "center"}
                ]
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": button_rows
            }
        }
    }

# 🔥 เลือก type → สุ่ม 4 เมนู
def build_food_list(type_name):
    food_list = foods[type_name]
    random_foods = random.sample(food_list, min(3, len(food_list)))

    bubbles = []
    for food in random_foods:
        bubbles.append({
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": food["image"],
                "size": "full",
                "aspectMode": "cover",   # บีบเต็ม
                "aspectRatio": "16:9"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": food["name"], "weight": "bold", "size": "md", "wrap": True},
                    {"type": "text", "text": f"พลังงาน: {food['nutrition']}"},
                    {"type": "text", "text": f"โปรตีน: {food['protein']}"}
                ]
            }
        })

    return {
        "type": "flex",
        "altText": f"เมนู {type_name}",
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
                "aspectMode": "cover",  # บีบเต็ม
                "aspectRatio": "16:9"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {"type": "text", "text": s["name"], "weight": "bold", "size": "lg", "wrap": True}
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#00AA00",
                        "action": {"type": "uri", "label": "เปิดแผนที่", "uri": s["location"]}
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
        headers={"Authorization": f"Bearer {LINE_TOKEN}", "Content-Type": "application/json"},
        json={"replyToken": reply_token, "messages": [message]}
    )

# ================== WEBHOOK ==================
@app.post("/webhook")
async def webhook(req: Request):
    body = await req.json()

    # ตรวจสอบ event มีไหม
    if "events" not in body or len(body["events"]) == 0:
        return {"status": "ok"}

    event = body["events"][0]
    reply_token = event.get("replyToken")
    if not reply_token:
        return {"status": "ok"}

    # ตอบกลับ follow event
    if event.get("type") == "follow":
        reply(reply_token, add_quick_reply({"type": "text", "text": "ยินดีต้อนรับ 😄"}))
        return {"status": "ok"}

    # ถ้าไม่ใช่ message event
    if event.get("type") != "message":
        return {"status": "ok"}

    # ตรวจสอบว่าเป็นข้อความจริง ๆ
    message_type = event["message"].get("type")
    if message_type != "text":
        # กรณีเป็น sticker, image, video, audio, location ฯลฯ
        reply(reply_token, add_quick_reply({
            "type": "text",
            "text": "ฉันไม่เข้าใจ"
        }))
        return {"status": "ok"}

    # ได้ข้อความจริง ๆ
    text = event["message"].get("text", "").strip()
    if not text:
        reply(reply_token, add_quick_reply({
            "type": "text",
            "text": "ฉันไม่เข้าใจ"
        }))
        return {"status": "ok"}

    # ตรวจสอบ intent ตามปกติ
    intent = detect_intent(text)

    # 🔥 ตอบกลับตาม intent
    if intent == "random_food" or intent == "hungry":
        message = build_random_3_foods()
    elif intent == "recommend_food":
        message = build_type_flex()
    elif intent == "choose_type":  # เลือกประเภท → สุ่ม 4 เมนู
        message = build_food_list(text)
    elif text == "สุ่มอาหาร":  # สุ่มอาหารเอง
        message = build_random_3_foods()
    elif intent == "recommend_restaurant":
        message = build_shop_flex()
    elif intent == "not_hungry":
        message = {"type": "text", "text": "ฉันไม่เข้าใจ"}
    else:
        message = {"type": "text", "text": "ฉันไม่เข้าใจ"}

    # reply พร้อม quick reply
    reply(reply_token, add_quick_reply(message))
    return {"status": "ok"}