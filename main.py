from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ImageSendMessage
)
import os
from dotenv import load_dotenv
import random
from openai import OpenAI
import time
from typing import Optional, Tuple

# 環境変数の読み込み
load_dotenv()

# Flaskのインスタンスを作成
app = Flask(__name__)

# LINE Botの設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 画像ハンドラークラス
class ImageHandler:
    def __init__(self):
        self.base_url = "https://storage.googleapis.com/sasaki-images-bot"
        self.morning_images = [f"morning/{i}.jpg" for i in range(1, 9)]
        self.evening_images = [f"evening/{i}.jpg" for i in range(1, 9)]

    def get_random_image(self, time_slot: str) -> str:
        if time_slot == 'morning':
            image_path = random.choice(self.morning_images)
        else:
            image_path = random.choice(self.evening_images)
        return f"{self.base_url}/{image_path}"

    def should_send_image(self, message: str) -> Tuple[bool, str]:
        if any(word in message.lower() for word in ["おはよう", "おはようございます", "グッドモーニング"]):
            return (True, "morning")
        if any(word in message.lower() for word in ["おつかれ", "お疲れ", "疲れた", "つかれた", 
                                          "飲み", "のみ", "お酒", "日本酒", "ビール"]):
            return (True, "evening")
        return (False, "")

[以下、既存のURL定数定義とresponses定義は完全に維持]

def get_chatgpt_response(user_message: str) -> Optional[str]:
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=10.0
        )
        
        system_prompt = """あなたは「咲々木 花」として振る舞ってください。
[既存のシステムプロンプトをそのまま維持]"""
        
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500,
            presence_penalty=0.6,
            frequency_penalty=0.4
        )
        
        full_response = response.choices[0].message.content
        
        if len(full_response) > 4000:
            sentences = full_response.split('。')
            truncated_response = ''
            for sentence in sentences:
                if len(truncated_response + sentence + '。') < 4000:
                    truncated_response += sentence + '。'
                else:
                    break
            return truncated_response + "\n（続きは少し短くお話しするね💕）"
        
        return full_response

    except Exception as e:
        print(f"ChatGPT error: {str(e)}")
        return None

[get_appropriate_response関数は既存のまま維持]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        user_message = event.message.text
        text_response = get_appropriate_response(user_message)
        
        # 画像送信の判断
        image_handler = ImageHandler()
        should_send, time_slot = image_handler.should_send_image(user_message)
        
        if should_send:
            image_url = image_handler.get_random_image(time_slot)
            messages = [
                TextSendMessage(text=text_response),
                ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                )
            ]
        else:
            messages = [TextSendMessage(text=text_response)]
        
        line_bot_api.reply_message(event.reply_token, messages)
        
    except Exception as e:
        print(f"Error in handle_message: {str(e)}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ごめんね、うまく話せなかったの...😢")
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
