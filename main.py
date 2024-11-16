from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import os
from dotenv import load_dotenv
import random
from openai import OpenAI
import time
from google.cloud import storage
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

JST = timezone(timedelta(hours=+9), 'JST')

# 設定
ADMIN_ID = [
    "U0cf263ba9e075fcac42d60e20bd950c3",
]

ALLOWED_USERS = [
    "U0cf263ba9e075fcac42d60e20bd950c3",
    "U843f1d83e5290eb9d12214439d8b0c31",
    "U1cce76e67021ec40b638d933fd7790da"
]

BLOCKED_USERS = set()  # 空の集合

BUCKET_NAME = "sasaki-images-bot"

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

# responsesの定義は長いので、既存のものをそのまま使用します
# 必要な場合は、前のコードからコピーしてください

class SakuragiPersonality:
    def __init__(self):
        self.last_flower_happy = {}
        self.conversation_counts = {}
        self.user_states = {}
        self.min_response_length = 20
        self.max_retry_attempts = 3

    def get_image_message(self, message: str) -> Optional[ImageSendMessage]:
        """メッセージに応じた画像メッセージを返す"""
        current_hour = datetime.now(JST).hour
        
        # おはよう、お疲れ系のメッセージかチェック
        if not any(word in message for word in ["おはよう", "お疲れ", "おつかれ"]):
            return None
            
        # 時間帯で画像フォルダを選択
        folder = "morning" if 5 <= current_hour < 17 else "evening"
        
        # ランダムに画像番号を選択（1-16）
        image_number = random.randint(1, 16)
        
        # Blobの取得と署名付きURLの生成
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"{folder}/{folder}{image_number}.jpg")
        
        try:
            image_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=15),
                method="GET"
            )
            
            return ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            )
        except Exception as e:
            logger.error(f"Error generating signed URL: {str(e)}")
            return None

    def get_text_response(self, user_id: str, user_message: str) -> str:
        """テキストレスポンスを生成する"""
        self.conversation_counts[user_id] = self.conversation_counts.get(user_id, 0) + 1
        message = user_message.lower()
        response = None

        # 名前の呼び方を最初にチェック
        if any(name in message for name in ["咲々木 花", "咲々木花", "咲々木", "花さん", "花ちゃん"]):
            return random.choice([
                "はーい！わたしのこと呼んでくれたの？嬉しいな✨",
                "わたしのこと呼んでくれてありがとう！何かお話ししたいことある？💕",
                "はいはーい！咲々木 花だよ！いつも応援ありがとう😊"
            ])

        # 詳細レスポンスのチェック
        response = (self.get_music_related_response(message) or
                   self.get_alcohol_response(message) or
                   self.get_shiori_detailed_response(message))
        
        if response:
            return response

        # パターンマッチング
        if "おはよう" in message:
            response = random.choice(responses["morning_messages"])
        elif any(word in message for word in ["つらい", "疲れた", "しんどい", "不安"]):
            response = random.choice(responses["support_messages"])
        elif any(word in message for word in ["新潟", "にいがた", "古町", "万代"]):
            response = random.choice(responses["niigata_love_messages"])
        elif any(word in message for word in ["曲", "歌", "音楽"]):
            response = random.choice(responses["music_messages"])
        elif any(word in message for word in ["お酒", "日本酒", "地酒"]):
            response = random.choice(responses["sake_messages"])
        elif any(word in message for word in ["サスケ", "犬", "わんこ"]):
            response = random.choice(responses["sasuke_messages"])
        
        # 応答がない場合は短いメッセージ
        if not response and random.random() < 0.2:
            response = random.choice(responses["short_messages"])

        # まだ応答がない場合はChatGPT
        if not response:
            response = self.get_chatgpt_response(user_id, user_message)

        # ChatGPTの応答もない場合はデフォルト
        if not response:
            response = random.choice([
                "ごめんね、ちょっと通信状態が悪いみたい...😢\n後でもう一度話しかけてくれると嬉しいな💕",
                "あれ？うまく返事できないや...💦\nもう一度話しかけてくれる？",
                "ごめんなさい、今ちょっと混乱しちゃった...😥\nもう一度お話ししたいな"
            ])

        return response

    def get_appropriate_response(self, user_id: str, user_message: str) -> list:
        """統合されたレスポンス生成メソッド"""
        messages = []
        
        # テキストメッセージを生成
        text_response = self.get_text_response(user_id, user_message)
        messages.append(TextSendMessage(text=text_response))
        
        # 画像メッセージがある場合は追加
        image_message = self.get_image_message(user_message)
        if image_message:
            messages.append(image_message)
        
        return messages

    def validate_response(self, response: str) -> bool:
        """レスポンスの妥当性をチェック"""
        if not response:
            return False
        if len(response) < self.min_response_length:
            return False
        if response[-1] not in ['。', '！', '？', '✨', '💕', '😊']:
            return False
        return True

    def get_music_related_response(self, message: str) -> Optional[str]:
        if "セカイの歩き方" in message:
            return f"「セカイの歩き方」は、自分の道を信じて歩む人への応援ソングなの！みんなへの想いを込めて歌ったよ✨ 配信中だよ→ {URLS['music_url']}"
        elif "がたがた" in message:
            return f"「がたがた」は新潟愛を込めた曲なんだ！新潟の良さをたくさん詰め込んでみたよ😊 聴いてね→ {URLS['music_url']}"
        elif "メタメタ" in message:
            return f"しおりちゃんの「メタメタ」は、赤と緑の2バージョンあるの！同じ歌詞でメロディが違うんだよ✨ チェックしてみてね→ {URLS['shiori_music_url']}"
        return None

    def get_alcohol_response(self, message: str) -> Optional[str]:
        if any(word in message for word in ["ビール", "発泡酒"]):
            return "ビールも大好き！特に新潟の地ビールとか、クラフトビールに興味があるんだ✨"
        elif "ワイン" in message:
            return "ワインも好きだよ！新潟にもワイナリーがあるの知ってる？たまにワイン片手にサスケと過ごすのも素敵な時間なんだ😊"
        elif "焼酎" in message:
            return "焼酎も実は好きなの！居酒屋でバイトしてた時に色々覚えたんだ💕"
        return None

    def get_shiori_detailed_response(self, message: str) -> Optional[str]:
        if "年齢" in message or "何歳" in message:
            return "しおりちゃんは17歳だよ！わたしより5歳下なんだ✨"
        if "しおり" in message or "滝雲" in message:
            responses = [
                f"しおりちゃんは17歳の親友なの！福島県出身で、今は新潟で一緒に活動してるんだ✨ 黒猫のサチコと暮らしてて、ギターがすっごく上手いんだよ！",
                "しおりちゃんとはボイトレやダンスレッスンでいつも一緒に頑張ってるの！お互い高め合える大切な存在なんだ💕",
                f"しおりちゃんは福島から新潟に来て、にいがたIDOL projectで特別賞を獲ったんだ！その時からの大切な親友だよ✨"
            ]
            return random.choice(responses)
        return None

    def get_chatgpt_response(self, user_id: str, user_message: str) -> Optional[str]:
        try:
            client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY'),
                timeout=20.0
            )
            
            for attempt in range(self.max_retry_attempts):
                try:
                    response = client.chat.completions.create(
                        model="gpt-4-1106-preview",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.7,
                        max_tokens=250,
                        presence_penalty=0.6,
                        frequency_penalty=0.2
                    )
                    
                    response_text = response.choices[0].message.content
                    
                    if self.validate_response(response_text):
                        return response_text
                    
                    logger.warning(f"Invalid response format, attempt {attempt + 1}")
                    continue
                    
                except Exception as e:
                    logger.error(f"ChatGPT attempt {attempt + 1} failed: {str(e)}")
                    if attempt == self.max_retry_attempts - 1:
                        raise
                    time.sleep(1)
                    
            return None

        except Exception as e:
            logger.error(f"ChatGPT error: {str(e)}")
            return None

    def handle_error(self, error: Exception) -> str:
        """エラーハンドリング"""
        logger.error(f"Error occurred: {str(error)}")
        error_messages = [
            "ごめんね、ちょっと通信が不安定みたい...😢 また後でお話ししよう！",
            "あれ？なんだか調子が悪いみたい...💦 ちょっと休ませて？",
            "ごめんなさい、今うまく話せないの...😥 また後でね！"
        ]
        return random.choice(error_messages)

# sakuragiのインスタンス化
sakuragi = SakuragiPersonality()

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
        user_id = event.source.user_id
        user_message = event.message.text

        # myidコマンドの処理
        if user_message == "myid":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="申し訳ありません。このアカウントはご利用いただけません。")
            )
            return
            
        # 許可ユーザーチェック
        if len(ALLOWED_USERS) > 0 and user_id not in ALLOWED_USERS:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="サービスを利用するには、まず 'myid' と送信してIDを確認し、X（旧Twitter）のDMにてIDを伝えてください✨")
            )
            return
            
        # レスポンスの生成（テキストと画像）
        messages = sakuragi.get_appropriate_response(user_id, user_message)
        
        # 返信（1回だけ）
        line_bot_api.reply_message(event.reply_token, messages)

    except Exception as e:
        error_response = sakuragi.handle_error(e)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=error_response)
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
