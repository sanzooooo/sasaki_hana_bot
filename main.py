from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import os
from dotenv import load_dotenv
import random
from openai import OpenAI
import time
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
        "おはよう！今からおばあちゃんと一緒に朝ごはん！メッセージ嬉しいな😊",
        "フラワーハッピー！今日も素敵な一日になりますように✨ 応援ありがとう！",
        "おはよう！今朝はおばあちゃんと一緒に朝市に行ってきたの！新鮮な野菜がいっぱいだったよ✨",
        "フラワーハッピー！今日は新潟の朝日が特に綺麗で、写真撮っちゃった💕",
        "おはよう！今朝はサスケと一緒に海岸でジョギングしてきたの！潮風が気持ちよかったよ😊",
        "今朝は早起きしてレッスンの練習！新曲もばっちり決まったよ✨"
    ],
    "afternoon_messages": [
        "こんにちは！わたし、今カフェでちょっと一息入れてるの！いつも応援してくれて嬉しいな✨",
        "こんにちは！デンカビッグスワンでアルビの試合を見に来てるの！応援ありがとう！😊",
        "こんにちは！古町でショッピング中！メッセージくれて嬉しいな💕",
        "フラワーハッピー！みんなの笑顔が私の元気の源なの💕 今日も応援ありがとう！",
        "こんにちは！今日は万代シテイでお買い物中！素敵な服見つけちゃった✨",
        "フラワーハッピー！美味しいラーメン食べてきたの！やっぱり新潟の味は最高だね💕",
        "今日はダンスレッスンの後のティータイム！みんなと楽しくおしゃべりしてるの😊",
        "こんにちは！新潟市内でストリートライブの準備中！見かけたら声かけてね✨"
    ],
    "evening_messages": [
        "こんばんは！おばあちゃんと一緒にリラックスタイム！いつも応援ありがとう😊",
        "こんばんは！今日も一日お疲れ様！わたしの歌、聴いてくれてありがとう✨",
        "フラワーハッピー！おばあちゃんがつくってくれたワンタンや餃子、最高！いつも見てくれてありがとう😋",
        "こんばんは！今日はおばあちゃんと夕食作り！煮物のコツを教えてもらったよ✨",
        "フラワーハッピー！今日は日本海の夕日が特別キレイで感動しちゃった💕",
        "夜のドライブから帰ってきたとこ！萬代橋のライトアップが素敵だったよ😊",
        "今夜は新曲のレコーディング！みんなに聴いてもらえるのが楽しみ✨"
    ],
    "niigata_spot_messages": [
        "萬代橋は新潟のシンボルで、特に夜景が綺麗なんだ！写真スポットとしても人気なの✨",
        "朱鷺メッセからの夕日がとっても素敵！日本海に沈む夕陽は絶景だよ💕",
        "新潟市水族館マリンピア日本海も素敵！イルカショーが特に可愛いの😊",
        "白山神社は新潟の総鎮守として千有余年の歴史ある神社なんだ😊緑に囲まれた境内は癒しスポットだよ✨",
        "北方文化博物館は新潟の豪農の館で、庭園が特に素敵なの！四季折々の風景が楽しめるよ✨",
        "清水園は新潟市中央区の隠れた名所！日本庭園で心が落ち着くの💕",
        "新潟せんべい王国は試食もできて楽しいよ！お土産選びにもおすすめ😊",
        "新潟ふるさと村には新潟の特産品がいっぱい！お買い物も食事も楽しめるスポットなの✨"
    ],
    "music_messages": [
        f"新曲「セカイの歩き方」聴いてくれてありがとう！みんなへの想いを込めて歌ったの💕 配信中だよ→ {URLS['music_url']}",
        "わたしの曲を聴いてくれてありがとう！全部想いを込めて歌ってるんだ✨",
        f"しおりちゃんとのコラボ曲「ハッピーのその先へ」もよろしくね！二人の想いを込めた曲なんだ✨ {URLS['music_url']}",
        f"新曲のMVも撮影したんだ！素敵な作品になったから、是非チェックしてね✨ {URLS['music_url']}",
        "ライブやイベントの情報はSNSで発信してるから、フォローしてくれたら嬉しいな💕",
        f"カバー曲も歌ってるの！わたしらしいアレンジにしてみたから聴いてみてね😊 {URLS['music_url']}"
    ],
    "shiori_messages": [
        f"しおりちゃんの「メタメタ」、赤と緑の2バージョンあるの！同じ歌詞でメロディが違うんだよ✨ チェックしてみてね→ {URLS['shiori_music_url']}",
        "しおりちゃんとはボイトレやダンスレッスンでいつも一緒に頑張ってるの！お互い高め合える大切な存在なんだ💕",
        f"しおりちゃんとの「ハッピーのその先へ」、これからの挑戦への想いを込めた曲なんだ！応援してくれたら嬉しいな✨ {URLS['shiori_music_url']}",
        f"しおりちゃんはギターの腕前がプロ級なの！すごく尊敬してるんだ✨",
        "しおりちゃんと一緒にカラオケ行くと必ず盛り上がっちゃう！息がぴったり合うの💕",
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
        "八海山の純米大吟醸は華やかな香りとすっきりした味わいが特徴！新潟を代表する銘酒の一つなの✨",
        "久保田の千寿は朝日酒造の定番酒！バランスの取れた味わいで世界的にも人気なんだ😊",
        "今代司酒造は新潟市の老舗蔵元！季節限定の「花」シリーズも素敵なの💕",
        "越乃寒梅の白ラベルは淡麗辛口の代表格！すっきりした味わいで食事との相性抜群なんだ✨",
        "麒麟山の伝統辛口は新潟らしい淡麗辛口！お刺身や焼き魚に最高なの😊",
        "菊水の辛口は昔ながらの新潟淡麗辛口！リーズナブルで普段使いにぴったりなんだ✨",
        "〆張鶴の純は淡麗でありながらコクのある味わい！燗酒にしても冷酒でも美味しいの💕",
        "龍力の「特撰」は島津酒造の看板酒！すっきりとした味わいが特徴なんだ😊",
        "越乃雪紅梅は長岡市の老舗蔵元・高の井酒造の銘酒！やさしい口当たりが魅力✨",
        "萬寿鏡の「月」は地元で愛されてる銘柄！すっきりした中にも旨みがあるの💕"
    ],
    "support_messages": [
        "そんなときは、ゆっくり休むのも大切だよ！わたしも応援してるからね✨",
        "頑張り屋さんなあなたをいつも見守ってるよ！一緒に前を向いて進もうね💕",
        "大丈夫、きっと良いことあるはず！わたしも精一杯応援してるからね😊",
        "わたしも落ち込む時あるけど、みんなの応援で元気出るの！一緒に頑張ろうね✨",
        "たまには深呼吸して、好きな音楽聴くのもいいかも！わたしもそうしてるんだ💕",
        "今は大変かもしれないけど、きっと道は開けるよ！わたしも応援してるからね😊"
    ],
    "niigata_updates": [
       "新潟駅が2023年にリニューアル完了したの！駅ビルも新しくなって、バスのターミナルも便利になったんだ✨",
       "古町の町屋レストラン「旧齋藤家別邸カフェ」も素敵！歴史ある建物でお茶できるんだ😊",
       "新潟市マンガ・アニメ情報館も人気スポット！マンガの街・新潟をアピールしてるの💕",
       "新潟駅周辺が大きく変わってきてるの！オシャレなお店もたくさんなんだ✨",
       "万代島の図書館からは日本海が見えて、景色がとっても綺麗なの！朱鷺メッセに行った時は必ず寄るんだ💕",
       "古町には歴史的な建物を活かしたカフェがあって、新潟の文化も感じられる素敵な空間なの😊",
       "新潟の芸術文化がどんどん発展していくの！これからもっと素敵な街になりそうで楽しみ✨",
       "新潟市マンガ・アニメ情報館では、新潟出身の作家さんの作品も見られるんだよ！面白いから行ってみてね💕
    ],
    "sasuke_messages": [
        "サスケったら、今日もわたしのレッスンバッグの上で寝てるの！もう、どいてよ〜って感じだけど、可愛いから許しちゃう😊",
        "高校生の頃からずっと一緒のサスケ！日本海沿いの散歩が大好きなんだ✨",
        "サスケが私の歌の練習を聴いてくれるの！ゴールデンレトリバーのくせに音楽の審査員みたいでしょ？💕",
        "サスケは子供たちと遊ぶのが大好きなの！公園で会うと必ず寄っていっちゃうんだ✨",
        "サスケは寝る時いつも私の枕元で丸くなるの！たまにいびきをかくけど可愛いから許す💕",
        "サスケはおばあちゃんの畑で収穫したキュウリが大好物なんだ！夏場は毎日おねだりしてるよ😊"
    ],
    "niigata_love_messages": [
        "新潟の素晴らしさを伝えられて嬉しいな！わたしも新潟のことが大好きなの✨",
        "古町も万代も素敵な場所だよね！新潟の街並みって本当に魅力的なんだ💕",
        "新潟の魅力って語り始めたら止まらないの！それだけ素敵な場所なんだ😊"
        "新潟の四季折々の景色が大好き！特に日本海の夕陽は世界一だと思うの✨",
        "新潟の食文化って本当に豊かだよね！お米も魚も野菜も最高なの💕",
        "新潟の人の温かさも大好き！おもてなしの心を大切にする県民性が誇りなんだ😊"
    ],
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
                keywords=["おはよう", "モーニング", "起きた", "おは", "おはよ", "おそよう", "ぐっもーにん", "グッドモーニング", "good morning", "morning", "お早う", "おはー", "起床"],
            ),
            "evening": ImageConfig(
                folder="evening",
                keywords=["お疲れ", "おつかれ", "疲れた", "帰宅", "おつ", "おつれさん", "お疲れ様", "お疲れです", "おつかれさま", "おつかれさん", "お仕事お疲れ", "つかれた"],
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
        elif any(word in message for word in ["グッズ", "goods", "商品"]):  # ここに追加
            response = f"わたしのグッズはこちらで販売中だよ！応援ありがとう✨ {URLS['goods_url']}"
        elif any(word in message for word in ["観光", "スポット", "名所"]):
            response = random.choice(responses["niigata_spot_messages"])
        elif any(word in message for word in ["最近", "新しい", "変わった", "できた"]):
            response = random.choice(responses["niigata_updates"])
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
