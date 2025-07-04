import json
from flask import Flask, request
from dotenv import load_dotenv
import os
import requests
import re
import logging  

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
load_dotenv()

PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')  
CHATBOT_API_URL = os.getenv('CHATBOT_API_URL')

# --- Pre-processing/Post-processing Functions ---
def postprocess_chatbot_response(response_text):
    response_text = re.sub(r"</?b>", "", response_text)
    response_text = re.sub(r"</?u>", "", response_text)
    response_text = re.sub(r"\*", "", response_text)

    # Convert Markdown-style links to plain URLs
    response_text = re.sub(r'\[.*?\]\((https?://[^\)]+)\)', r'\1', response_text)

    # Beautify lines like "*Step 1:*" → "🔹 STEP 1:"
    response_text = re.sub(r"(?:•\s*)?\*?Step\s*(\d+):\*?", r"🔹 STEP \1:", response_text, flags=re.IGNORECASE)
    response_text = re.sub(r"•\s*", "• ", response_text)

    # Capitalize common headers
    response_text = re.sub(r"(?i)(owner information)", r"📍 \1".upper(), response_text)
    response_text = re.sub(r"(?i)(restaurant details)", r"🍽️ \1".upper(), response_text)
    response_text = re.sub(r"(?i)(finalize & verify)", r"✅ \1".upper(), response_text)
    response_text = re.sub(r"\n{2,}", "\n\n", response_text)
    
    response_text = re.sub(r"<br\s*/?>", "\n", response_text, flags=re.IGNORECASE)
    
    return response_text.strip()


def get_chatbot_reply(message_text, user_language="en"):
    try:
        payload = {
            "question": message_text,
            "language": user_language
        }
        headers = {'Content-Type': 'application/json'}

        logging.info(f"Sending message to chatbot API: {CHATBOT_API_URL} with payload: {payload}")
        response = requests.post(CHATBOT_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            model_output = response.json()
            raw_reply = model_output.get("answer", "")
            print(f"Raw reply from chatbot API: {raw_reply}")
            return postprocess_chatbot_response(raw_reply)
        else:
            logging.error(f"Chatbot API error (Status: {response.status_code}): {response.text}")
            return "Apologies, the FoodChow Assistant is currently experiencing a technical issue. Please try again later or contact support."
    except requests.exceptions.ConnectionError as ce:
        logging.error(f"Connection error to chatbot API at {CHATBOT_API_URL}: {ce}. Is the chatbot API running?")
        return "I'm having trouble connecting to my knowledge base right now. Please check back in a moment or contact FoodChow support."
    except Exception as e:
        logging.error(f"Unexpected error while calling chatbot API: {e}", exc_info=True)
        return "An unexpected error occurred. Please try again or contact FoodChow support."


def send_messenger_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v18.0/me/messages"
    headers = {'Content-Type': 'application/json'}
    params = {'access_token': PAGE_ACCESS_TOKEN}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    logging.info(f"Sending message to Messenger API for recipient {recipient_id}")
    response = requests.post(url, headers=headers, params=params, json=payload)
    logging.info(f"Messenger API response: Status {response.status_code}, Text: {response.text}")
    return response


@app.route('/')
def home():
    return "FoodChow Messenger Bot is running!", 200


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == "subscribe" and token == VERIFY_TOKEN:
            logging.info("WEBHOOK VERIFIED successfully.")
            return challenge, 200
        else:
            logging.warning("WEBHOOK VERIFICATION FAILED: Token mismatch or invalid mode.")
            return "Verification failed", 403

    elif request.method == 'POST':
        data = request.get_json()

        try:
            if data.get("object") == "page":
                logging.info("in page")
                
                for entry in data.get("entry", []):
                    for messaging_event in entry.get("messaging", []):
                        sender_id = messaging_event["sender"]["id"]

                        # 🛑 Ignore echo messages (Facebook sends these when the bot itself replies)
                        if messaging_event.get("message", {}).get("is_echo"):
                            logging.info("Ignored echo message (bot's own message).")
                            continue

                        # ✅ Handle actual user text messages
                        if "message" in messaging_event and "text" in messaging_event["message"]:
                            message_text = messaging_event["message"]["text"]
                            logging.info(f"Received text message from {sender_id}: '{message_text}'")

                            bot_response = get_chatbot_reply(message_text)
                            send_messenger_message(sender_id, bot_response)

                        else:
                            logging.info(f"Ignored non-text or unsupported message event: {json.dumps(messaging_event, indent=2)}")

        except Exception as e:
            logging.error(f"Error processing webhook event: {e}", exc_info=True)

        return "EVENT_RECEIVED", 200


if __name__ == '__main__':
    app.run(host='195.201.175.72', port=5003)
