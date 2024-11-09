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
from typing import Optional
from datetime import datetime

# 環境変数の読み込み
load_dotenv()

# Flaskのインスタンスを作成
app = Flask(__name__)

# LINE Botの設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# URL定数の定義
URLS = {
    'music_url': "https://www.tunecore.co.jp/artists?id=877913",
    'line_stamp_url': "https://store.line.me/stickershop/product/26678877/ja",
    'note_url': "https://note.com/sasuke_wanko",
    'twitter_url': "https://x.com/sasuke_wanko",
    'goods_url': "https://suzuri.jp/sasuke_wanko",
    'shiori_music_url': "https://www.tunecore.co.jp/artists/shiori_takigumo",
    'shiori_line_url': "https://store.line.me/stickershop/product/27505343/ja",
    'shiori_note_url': "https://note.com/shiori_takigumo",
    'shiori_twitter_url': "https://x.com/shiori_takigumo",
    'shiori_goods_url': "https://suzuri.jp/sasuke_wanko"
}

# メッセージカウンター（URL共有用）
message_counter = 0

# 画像ハンドラークラス
class ImageHandler:
    def __init__(self):
        self.base_url = "https://storage.googleapis.com/sasaki-images"
        self.morning_images = [f"morning/{i}.jpg" for i in range(1, 11)]
        self.evening_images = [f"evening/{i}.jpg" for i in range(1, 11)]

    def get_random_image(self, time_slot: str) -> str:
        """ランダムに画像URLを取得"""
        if time_slot == 'morning':
            image_path = random.choice(self.morning_images)
        else:
            image_path = random.choice(self.evening_images)
        return f"{self.base_url}/{image_path}"

    def should_send_image(self, message: str) -> tuple[bool, str]:
        """画像を送信すべきか判断"""
        # 朝の挨拶パターン
        if any(word in message for word in ["おはよう", "おはようございます", "グッドモーニング"]):
            return True, "morning"
        
        # お疲れ様パターン
        if any(word in message for word in ["おつかれ", "お疲れ", "疲れた", "つかれた", 
                                          "飲み", "のみ", "お酒", "日本酒", "ビール"]):
            return True, "evening"
        
        return False, ""

# 応答メッセージの定義
responses = {
    "morning_messages": [
        "おはよう！今日も新潟は素敵な朝だよ！いつも応援ありがとう😊✨",
        "わたし、今朝はサスケと日本海沿いを散歩してきたの！いつも見守ってくれてありがとう✨",
        "おはよう！わたし、新潟駅前のカフェでモーニング中！メッセージ嬉しいな😊"
    ],
    "afternoon_messages": [
        "こんにちは！わたし、今カフェでちょっと一息入れてるの！いつも応援してくれて嬉しいな✨",
        "こんにちは！デンカビッグスワンでアルビの試合を見に来てるの！応援ありがとう！😊",
        "こんにちは！古町でショッピング中！メッセージくれて嬉しいな💕"
    ],
    "evening_messages": [
        "こんばんは！いつも応援ありがとう！わたし、今お気に入りの本読んでリラックスタイム😊",
        "こんばんは！今日も一日お疲れ様！わたしの歌、聴いてくれてありがとう✨",
        "こんばんは！おばあちゃんが作ってくれた水餃子、最高だったよ！いつも見てくれてありがとう😋"
    ],
    # ... [他のresponsesは変更なし]
}

def get_chatgpt_response(user_message: str) -> Optional[str]:
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=10.0
        )
        
        system_prompt = """[既存のシステムプロンプトをそのまま維持]"""
        
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
        
        return response.choices[0].message.content

    except Exception as e:
        print(f"ChatGPT error: {str(e)}")
        return None

def get_appropriate_response(user_message: str) -> str:
    global message_counter
    message_counter += 1

    try:
        # パターンマッチングによる応答を試みる
        response = None
        message = user_message.lower()
        
        # 既存のパターンマッチング処理
        if "おはよう" in message:
            response = random.choice(responses["morning_messages"])
        elif "こんにちは" in message:
            response = random.choice(responses["afternoon_messages"])
        elif "こんばんは" in message:
            response = random.choice(responses["evening_messages"])
        elif any(word in message for word in ["つらい", "疲れた", "しんどい", "不安"]):
            response = random.choice(responses["support_messages"])
        elif any(word in message for word in ["新潟", "にいがた", "古町", "万代"]):
            response = random.choice(responses["niigata_love_messages"])
        elif any(word in message for word in ["曲", "歌", "音楽", "セカイの歩き方"]):
            response = random.choice(responses["music_messages"])
        elif any(word in message for word in ["東京", "表参道", "原宿", "渋谷"]):
            response = random.choice(responses["tokyo_activity_messages"])

        # パターンマッチングで応答がない場合はChatGPT
        if not response:
            response = get_chatgpt_response(user_message)
        
        # ChatGPTの応答がない場合はデフォルト
        if not response:
            response = random.choice(responses["default_messages"])
        
        # 応答の長さを確認と調整
        if len(response) > 4000:
            sentences = response.split('。')
            truncated_response = ''
            for sentence in sentences:
                if len(truncated_response + sentence + '。') < 4000:
                    truncated_response += sentence + '。'
                else:
                    break
            response = truncated_response + "\n（続きは少し短くお話しするね💕）"

        # URL追加処理
        if message_counter % 10 == 0:
            remaining_length = 4000 - len(response)
            if remaining_length > 100:
                url_additions = [
                    f"\nわたしの楽曲はここで聴けるよ！応援ありがとう✨ {URLS['music_url']}",
                    f"\nLINEスタンプ作ったの！使ってくれたら嬉しいな😊 {URLS['line_stamp_url']}",
                    f"\nいつも応援ありがとう！noteも読んでみてね💕 {URLS['note_url']}",
                    f"\n日々の活動はXで発信してるの！見てくれてありがとう✨ {URLS['twitter_url']}",
                    f"\nグッズも作ったの！見てくれて嬉しいな😊 {URLS['goods_url']}"
                ]
                response += random.choice(url_additions)
        
        return response

    except Exception as e:
        print(f"Response generation error: {str(e)}")
        return "ごめんね、うまく話せなかったの...😢 もう一度話しかけてくれる？"

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
