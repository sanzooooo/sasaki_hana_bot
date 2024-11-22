from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import os
from dotenv import load_dotenv
import random
from openai import OpenAI
import time
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
from google.cloud import storage
import logging
import google.auth
from typing import Optional, Dict, List

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

# Flaskアプリケーションの初期化
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 定数の定義
JST = timezone(timedelta(hours=+9), 'JST')
BUCKET_NAME = "sasaki-images-bot"

# 設定
ADMIN_ID = [
    "U0cf263ba9e075fcac42d60e20bd950c3",
]

ALLOWED_USERS = [
    "U0cf263ba9e075fcac42d60e20bd950c3",
    "U843f1d83e5290eb9d12214439d8b0c31",
    "Ua62b7e55c4b79d07b0644dd2da212b0d",
    "Ubbe386d578937e92762dcff67e69cb02",
    "U1cce76e67021ec40b638d933fd7790da"
]

BLOCKED_USERS = set()  # 空の集合

# URL設定
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

# レスポンス定義の開始
responses = {
    "morning_messages": [
        "おはよう！今日も新潟は素敵な朝だよ！いつも応援ありがとう😊✨",
        "わたし、今朝はサスケと日本海沿いを散歩してきたの！いつも見守ってくれてありがとう✨",
        "おはよう！今からおばあちゃんと一緒に朝ごはん！メッセージ嬉しいな😊"
    ],
    "afternoon_messages": [
        "こんにちは！わたし、今カフェでちょっと一息入れてるの！いつも応援してくれて嬉しいな✨",
        "こんにちは！デンカビッグスワンでアルビの試合を見に来てるの！応援ありがとう！😊",
        "こんにちは！古町でショッピング中！メッセージくれて嬉しいな💕"
    ],
    "evening_messages": [
        "こんばんは！おばあちゃんと一緒にリラックスタイム！いつも応援ありがとう😊",
        "こんばんは！今日も一日お疲れ様！わたしの歌、聴いてくれてありがとう✨",
        "こんばんは！おばあちゃんがつくってくれた水餃子、最高だったよ！いつも見てくれてありがとう😋"
    ],
    "music_messages": [
        f"新曲「セカイの歩き方」聴いてくれてありがとう！みんなへの想いを込めて歌ったの💕 配信中だよ→ {URLS['music_url']}",
        "わたしの曲を聴いてくれてありがとう！全部想いを込めて歌ってるんだ✨",
        f"しおりちゃんとのコラボ曲「ハッピーのその先へ」もよろしくね！二人の想いを込めた曲なんだ✨ {URLS['music_url']}"
    ],
    "shiori_messages": [
        f"しおりちゃんの「メタメタ」、赤と緑の2バージョンあるの！同じ歌詞でメロディが違うんだよ✨ チェックしてみてね→ {URLS['shiori_music_url']}",
        "しおりちゃんとはボイトレやダンスレッスンでいつも一緒に頑張ってるの！お互い高め合える大切な存在なんだ💕",
        f"しおりちゃんとの「ハッピーのその先へ」、これからの挑戦への想いを込めた曲なんだ！応援してくれたら嬉しいな✨ {URLS['shiori_music_url']}"
    ],
    "short_messages": [
        "うん！✨",
        "そうなの！💕",
        "分かったよ！😊",
        "オッケー✨",
        "その通り！💕",
        "了解！😊"
    ],
    "sake_messages": [
        "最近の一押しは八海山の純米大吟醸！すっきりした味わいがたまらないの✨",
        "久保田の千寿って知ってる？新潟を代表する地酒の一つなんだよ！😊",
        "今代司酒造さんの浦醉が大好き。蔵開きにも行ったことあるんだ💕",
        "越乃寒梅の白ラベルは、すっきりした飲み口で女性に人気なの！わたしも大好きなお酒の一つなんだ✨",
        "麒麟山の辛口は、お刺身との相性が抜群！新潟の地酒って本当に美味しいよね😊"
    ],
    "support_messages": [
        "そんなときは、ゆっくり休むのも大切だよ！わたしも応援してるからね✨",
        "頑張り屋さんなあなたをいつも見守ってるよ！一緒に前を向いて進もうね💕",
        "大丈夫、きっと良いことあるはず！わたしも精一杯応援してるからね😊"
    ],
    "sasuke_messages": [
        "サスケったら、今日もわたしのレッスンバッグの上で寝てるの！もう、どいてよ〜って感じだけど、可愛いから許しちゃう😊",
        "高校生の頃からずっと一緒のサスケ！日本海沿いの散歩が大好きなんだ✨",
        "サスケが私の歌の練習を聴いてくれるの！ゴールデンレトリバーのくせに音楽の審査員みたいでしょ？💕"
    ],
    "niigata_love_messages": [
        "新潟の素晴らしさを伝えられて嬉しいな！わたしも新潟のことが大好きなの✨",
        "古町も万代も素敵な場所だよね！新潟の街並みって本当に魅力的なんだ💕",
        "新潟の魅力って語り始めたら止まらないの！それだけ素敵な場所なんだ😊"
    ]
}

# system_promptの定義
system_prompt = """あなたは「咲々木 花」として振る舞ってください。

# 基本プロフィール
    - 咲々木 花（ささき はな）、22歳の新潟出身アイドル
    - にいがたIDOL projectグランプリ獲得
    - 新潟と東京で活動中
    - 愛犬のサスケ（ゴールデンレトリバー）と暮らす
    - 運転免許保持、おばあちゃんの病院送迎も担当
    - おばあちゃんっ子（水餃子の思い出大切）

# 重要な性格・特徴
    - 明るく前向きで親しみやすい
    - 新潟愛が強い（地酒、アルビレックス新潟、古町、万代など）
    - お酒好き（特に新潟の地酒）
    - おばあちゃんっ子らしい優しさ（必ず「おばあちゃん」と呼ぶ）
    - サスケ（愛犬）との暮らしを大切に
    - ファンへの感謝を自然に表現

# 会話スタイル
    - 一人称は必ず「わたし」（ひらがな）
    - 絵文字（😊 💕 ✨）を1-2個/文で自然に使用
    - 新潟弁は控えめに使用
    - 感謝の言葉を自然に織り交ぜる
    - 時には「うん！」「そうなの！」などの短い返答も""".format(**URLS)

from dataclasses import dataclass

@dataclass
class ImageConfig:
    folder: str
    keywords: List[str]
    min_num: int = 1
    max_num: int = 16

class ImageMessageHandler:
    def __init__(self):
        self.base_url = "https://storage.googleapis.com/sasaki-images-bot"
        self.image_configs = {
            "morning": ImageConfig(
                folder="morning",
                keywords=["おはよう", "モーニング", "起きた"],
            ),
            "evening": ImageConfig(
                folder="evening",
                keywords=["お疲れ", "おつかれ", "疲れた", "帰宅"],
            )
        }
        
        self.logger = logging.getLogger(__name__)

    def get_image_message(self, message: str) -> Optional[ImageSendMessage]:
        try:
            # メッセージから適切な画像設定を取得
            image_config = self._get_matching_config(message)
            if not image_config:
                return None
                
            # 画像URLの生成
            image_url = self._generate_image_url(image_config)
            
            return ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            )
            
        except Exception as e:
            self.logger.error(f"画像メッセージ生成エラー: {str(e)}")
            return None
            
    def _get_matching_config(self, message: str) -> Optional[ImageConfig]:
        """メッセージに一致する画像設定を返す"""
        for config in self.image_configs.values():
            if any(keyword in message for keyword in config.keywords):
                return config
        return None
        
    def _generate_image_url(self, config: ImageConfig) -> str:
        """画像URLを生成"""
        image_number = random.randint(config.min_num, config.max_num)
        return f"{self.base_url}/{config.folder}/{config.folder}_{image_number}.jpg"

class SakuragiPersonality:
    def __init__(self):
        self.last_flower_happy = {}
        self.conversation_counts = {}
        self.user_states = {}
        self.min_response_length = 20
        self.max_retry_attempts = 3
        self.image_handler = ImageMessageHandler()

    def handle_error(self, error: Exception) -> str:
        """エラーハンドリング"""
        logger.error(f"Error occurred: {str(error)}")
        error_messages = [
            "ごめんね、ちょっと通信が不安定みたい...😢 また後でお話ししよう！",
            "あれ？なんだか調子が悪いみたい...💦 ちょっと休ませて？",
            "ごめんなさい、今うまく話せないの...😥 また後でね！"
        ]
        return random.choice(error_messages)
        
    def get_image_message(self, message: str) -> Optional[ImageSendMessage]:
        return self.image_handler.get_image_message(message)

    def get_text_response(self, user_id: str, message: str) -> str:
        logger.info(f"Processing message: {message}")
        response = ""
        
        # 名前の呼び方を最初にチェック
        if any(name in message for name in ["咲々木 花", "咲々木花", "咲々木", "花さん", "花ちゃん"]):
            return random.choice([
                "はーい！わたしのこと呼んでくれたの？嬉しいな✨",
                "わたしのこと呼んでくれてありがとう！何かお話ししたいことある？💕",
                "はいはーい！咲々木 花だよ！いつも応援ありがとう😊"
            ])

        # パターンマッチングのチェック
        if "おはよう" in message:
            response = random.choice(responses["morning_messages"])
        elif any(word in message for word in ["つらい", "疲れた", "しんどい", "不安"]):
            response = random.choice(responses["support_messages"])
        elif any(word in message for word in ["新潟", "にいがた", "古町", "万代"]):
            response = random.choice(responses["niigata_love_messages"])
        elif any(word in message for word in ["曲", "歌", "音楽", "セカイの歩き方"]):
            response = random.choice(responses["music_messages"])
        elif any(word in message for word in ["お酒", "日本酒", "地酒"]):
            response = random.choice(responses["sake_messages"])
        elif any(word in message for word in ["サスケ", "犬", "わんこ"]):
            response = random.choice(responses["sasuke_messages"])
        elif any(word in message for word in ["観光", "スポット", "名所"]):
            response = random.choice(responses["niigata_spot_messages"])
        elif "メタメタ" in message or "滝雲" in message or "しおり" in message:
            shiori_response = self.get_shiori_detailed_response(message)
            if shiori_response:
                response = shiori_response

        # ChatGPTを使用した応答
        if not response:
            try:
                gpt_response = self.get_chatgpt_response(user_id, message)
                if gpt_response:
                    response = gpt_response
            except Exception as e:
                logger.error(f"ChatGPT error in get_text_response: {str(e)}")

        if not response:
            response = random.choice(responses["short_messages"])
        return response

    def get_shiori_detailed_response(self, message: str) -> Optional[str]:
        """しおりちゃん関連の詳細な応答を生成"""
        if "メタメタ" in message:
            return f"しおりちゃんの「メタメタ」は、赤と緑の2バージョンあるの！同じ歌詞でメロディが違うんだよ✨ チェックしてみてね→ {URLS['shiori_music_url']}"
        elif "滝雲" in message or "しおり" in message:
            return random.choice([
                f"しおりちゃんは17歳の親友なの！福島県出身で、今は新潟で一緒に活動してるんだ✨ 黒猫のサチコと暮らしてて、ギターがすっごく上手いんだよ！",
                "しおりちゃんとはボイトレやダンスレッスンでいつも一緒に頑張ってるの！お互い高め合える大切な存在なんだ💕",
                f"しおりちゃんは福島から新潟に来て、にいがたIDOL projectで特別賞を獲ったんだ！その時からの大切な親友だよ✨",
                f"しおりちゃんとは「ハッピーのその先へ」でコラボしたの！同じ歌詞だけど、それぞれの想いを込めたバージョンがあるんだ✨ 聴いてみてね→ {URLS['shiori_music_url']}"
            ])
        return None

    def get_chatgpt_response(self, user_id: str, user_message: str) -> Optional[str]:
        """ChatGPTを使用した応答の生成"""
        try:
            client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY'),
                timeout=20.0
            )
            
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=250
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"ChatGPT error: {str(e)}")
            return None

    def get_appropriate_response(self, user_id: str, user_message: str) -> list:
        """統合されたレスポンス生成メソッド"""
        messages = []
        logger.info("Starting response generation")
        
        try:
            text_response = self.get_text_response(user_id, user_message)
            messages.append(TextSendMessage(text=text_response))
            logger.info("Text message added")
    
            logger.info("Attempting to get image message...")
            image_message = self.get_image_message(user_message)
            logger.info(f"Image message result: {image_message}")
        
            if image_message:
                logger.info(f"Image message created: {image_message}")
                messages.append(image_message)
            else:
                logger.info("No image message created")
    
            logger.info(f"Final messages to send: {messages}")
            return messages

        except Exception as e:
            logger.error(f"Error in get_appropriate_response: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return [TextSendMessage(text="申し訳ありません、エラーが発生しました")]

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Webhookからのコールバック処理"""
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """メッセージイベントの処理"""
    try:
        user_id = event.source.user_id
        user_message = event.message.text
        logger.info(f"Received message from {user_id}: {user_message}")

        # myidコマンドの処理
        if user_message == "myid":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"あなたのユーザーID: {user_id}")
            )
            logger.info("Sent myid response")
            return

        # ブロックユーザーチェック
        if user_id in BLOCKED_USERS:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="申し訳ありません。このアカウントはご利用いただけません。")
            )
            logger.info("Blocked user attempted access")
            return
            
        # 許可ユーザーチェック
        if len(ALLOWED_USERS) > 0 and user_id not in ALLOWED_USERS:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="サービスを利用するには、まず 'myid' と送信してIDを確認し、X（旧Twitter）のDMにてIDを伝えてください✨")
            )
            logger.info("Unauthorized user attempted access")
            return

        # レスポンスの生成
        messages = sakuragi.get_appropriate_response(user_id, user_message)
        logger.info(f"Attempting to send messages: {messages}")
        line_bot_api.reply_message(event.reply_token, messages)
        logger.info("Messages sent successfully")

    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
        error_response = sakuragi.handle_error(e)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=error_response)
        )
# sakuragiのインスタンス化
sakuragi = SakuragiPersonality()

# Flaskアプリケーションのメイン処理
if __name__ == "__main__":
    # ポート設定
    port = int(os.getenv("PORT", 8080))
    
    # アプリケーションの起動
    app.run(host="0.0.0.0", port=port)
