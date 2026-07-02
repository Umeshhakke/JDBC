# app.py
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

HF_CHAT_URL = os.getenv("HF_CHAT_URL", "https://adcetcharbot-chatbot.hf.space/chat")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
GRAPH_API_VERSION = os.getenv("WHATSAPP_GRAPH_API_VERSION", "v25.0")

GRAPH_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{PHONE_NUMBER_ID}/messages"
processed_ids = set()

@app.route("/")
def home():
    return "Render WhatsApp Gateway Running"

@app.route("/health")
def health():
    return {"status":"ok"}

@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token")==VERIFY_TOKEN:
            return request.args.get("hub.challenge","")
        return "Verification failed",403

    data=request.get_json(silent=True) or {}
    try:
        value=data["entry"][0]["changes"][0]["value"]
        if "messages" not in value:
            return "ok",200

        msg=value["messages"][0]
        if msg.get("type")!="text":
            return "ok",200

        mid=msg["id"]
        if mid in processed_ids:
            return "ok",200
        processed_ids.add(mid)

        user=msg["from"]
        text=msg["text"]["body"]

        r=requests.post(HF_CHAT_URL,json={"message":text},timeout=120)
        r.raise_for_status()
        reply=r.json().get("reply","No response.")

        headers={
            "Authorization":f"Bearer {ACCESS_TOKEN}",
            "Content-Type":"application/json"
        }

        payload={
            "messaging_product":"whatsapp",
            "to":user,
            "type":"text",
            "text":{"body":reply[:4096]}
        }

        s=requests.post(GRAPH_URL,headers=headers,json=payload,timeout=30)
        print(s.status_code,s.text)

    except Exception as e:
        import traceback
        traceback.print_exc()

    return "ok",200

if __name__=="__main__":
    port=int(os.getenv("PORT",10000))
    app.run(host="0.0.0.0",port=port)
