from fastapi import FastAPI, Request
import requests
import random

app = FastAPI()

LINE_TOKEN = "+pIb40AfdSa2H+vIWscb871CSr4NWUmYPapSVLlYiPo7YcAia5OBDjrpmDzxmz9FQUKWCWkCf2hejHTjx8N1zacNmsPsGp50o5JqP+ce+5fMl2y9i0DxdFnNMStTjaRlw6OZPlqnFXWLayC3ls2D+gdB04t89/1O/w1cDnyilFU="


foods = {
    "ข้าวผัด": {
        "name": "ข้าวผัด",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ4fFZ_vPw78LgpzZRFhBH1t1ZoSESHvqiDKg&s",
        "nutrition": "350 kcal",
        "protein": "10 g"
    },
    "ส้มตำ": {
        "name": "ส้มตำ",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRhyKO0zPRsVyrUtoQczThJRI7LsSZuPRQLAQ&s",
        "nutrition": "120 kcal",
        "protein": "20 g"
    },
    "ผัดไทย": {
        "name": "ผัดไทย",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTFPPHTiVsSBK5Bp3ABHDWEMqTxkJlxb6Jwhw&s",
        "nutrition": "400 kcal",
        "protein": "30 g"
    },
    "ก๋วยเตี๋ยว": {
        "name": "ก๋วยเตี๋ยว",
        "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQcwaxuXmI8M0avMgvvNzLFjWtJ_HQ625xQSQ&s",
        "nutrition": "300 kcal",
        "protein": "20 g"
    }
}

shop = {
    "ร้านป้าไก่": {
        "name": "ร้านข้าวฟางคาเฟ่",
        "image": "https://lh3.googleusercontent.com/gps-cs-s/AHVAweoq5a9iTkwmHhhig-2ZLenFkjezPiNibxcurIzddT3LmaEdHn0uxsbUF6yW3rwTHMTONk2CtpthofyPrxVwjAgWxut19vyjBaXXrr4Y0cPZRuq7qjmHFNF5MTd_dBHc4-djDvHr=w408-h280-k-no",
        "location": "https://maps.app.goo.gl/YhdPqUhr2haR2zt16"
    },
    "ร้านป้าอาร์ต": {
        "name": "กิ๋นนี่เน้อ",
        "image": "https://lh3.googleusercontent.com/gps-cs-s/AHVAweq-e2B7HaRAo7hBxQlgxC4w-iwvwVkHAnxJuFE-fUIVdqRCBDICp5Nb8RbMCda6IamtGkOW2djU7ypsDv6e_fP6S431TvTAxmoIiNge4MhE3Xs6E9Nnx1IfcV0GuwFNGkKtRTZOCQ=w408-h725-k-no",
        "location": "https://maps.app.goo.gl/GmjiYYT6UPwFtpjS9"
    },
    "ร้านป้าเจ": {
        "name": "Term Waan cafe",
        "image": "https://lh3.googleusercontent.com/gps-cs-s/AHVAwer4jPAnZevWY8FeeICd50pduQpynaiad_sCa4RuPp7CMYQLGE1OOwoiXYmAOSpLWOg11IEqOpylCPWFJYtHyHhAUKmcG5RWBKxfX-UJSjPA_iVO7f01UDVoFYEAAuqIS6n18Yjf=w408-h408-k-no",
        "location": "https://maps.app.goo.gl/YZ5xKdpWobGBmBpa6"
    }
}

keywords = ["หิวข้าว", "กินอะไรดี"]

@app.post("/webhook")
async def webhook(req: Request):

    body = await req.json()
    event = body["events"][0]
    reply_token = event["replyToken"]

    if event["type"] != "message":
        message = {"type": "text", "text": "ฉันไม่เข้าใจ"}

    else:
        msg = event["message"]

        if msg["type"] != "text":
            message = {"type": "text", "text": "ฉันไม่เข้าใจ"}

        else:
            text = msg["text"]

            # แนะนำร้านอาหาร
            if text == "แนะนำร้านอาหาร":

                bubbles = []

                for s in shop.values():
                    bubbles.append({
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": s["name"],
                                    "weight": "bold",
                                    "size": "xl"
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
                                        "label": "เปิด Google Maps",
                                        "uri": s["location"]
                                    }
                                }
                            ]
                        }
                    })

                message = {
                    "type": "flex",
                    "altText": "ร้านอาหารแนะนำ",
                    "contents": {
                        "type": "carousel",
                        "contents": bubbles
                    }
                }

            else:

                food = None

                if text in keywords:
                    food = random.choice(list(foods.values()))

                if food:
                    message = {
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
                                    {
                                        "type": "text",
                                        "text": food["name"],
                                        "weight": "bold",
                                        "size": "xl"
                                    },
                                    {
                                        "type": "text",
                                        "text": f"พลังงาน: {food['nutrition']}"
                                    },
                                    {
                                        "type": "text",
                                        "text": f"โปรตีน: {food['protein']}"
                                    }
                                ]
                            }
                        }
                    }

                else:
                    message = {"type": "text", "text": "ฉันไม่เข้าใจ"}

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