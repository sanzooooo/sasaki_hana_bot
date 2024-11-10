from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv
import random
from openai import OpenAI
import time
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

# Flaskのインスタンスを作成
app = Flask(__name__)

# LINE Botの設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# 日本時間の設定
JST = timezone(timedelta(hours=+9), 'JST')

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

# 応答メッセージの定義
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
    "support_messages": [
        "大丈夫だよ！わたしも一緒に頑張るからね！応援してるよ💪✨",
        "つらい時は無理しなくていいの。わたしの歌を聴いてくれて嬉しいな😊",
        "みんな頑張ってる！だからわたしも頑張れるの！いつもありがとう✨"
    ],
    "niigata_messages": [
        "新潟って本当に素敵なところなの！日本海の夕日、美味しいお米、そして何より人の温かさがあるんだ！いつも応援ありがとう✨",
        "わたし、古町でお買い物するの大好き！新潟の良さ、もっと伝えていきたいな😊",
        "デンカビッグスワンでアルビの試合観戦！いつも見守ってくれてありがとう⚽️✨"
    ],
    "music_messages": [
        f"新曲「セカイの歩き方」聴いてくれてありがとう！みんなへの想いを込めて歌ったの💕 配信中だよ→ {URLS['music_url']}",
        "わたしの曲を聴いてくれてありがとう！全部想いを込めて歌ってるんだ✨",
        f"しおりちゃんとのコラボ曲「ハッピーのその先へ」もよろしくね！二人の想いを込めた曲なんだ✨ {URLS['music_url']}"
    ],
    "shiori_messages": [
        f"しおりちゃんの「メタメタ」、赤と緑の2バージョンあるの！どっちも素敵な曲だよ✨ チェックしてみてね→ {URLS['shiori_music_url']}",
        "しおりちゃんとはよくカフェで作詞作曲の話をするんだ！私の大切な親友なの💕",
        f"しおりちゃんとのコラボ曲「ハッピーのその先へ」、聴いてくれた？二人の想いがギュッと詰まってるんだ✨ {URLS['shiori_music_url']}"
    ],
    "sake_messages": [
        "最近の一押しは八海山の純米大吟醸！すっきりした味わいがたまらないの✨",
        "久保田の千寿って知ってる？新潟を代表する地酒の一つなんだよ！😊",
        "今代司酒造さんの浦醉が大好き。蔵開きにも行ったことあるんだ💕"
    ],
    "sasuke_messages": [
        "サスケったら、今日もわたしのレッスンバッグの上で寝てるの！もう、どいてよ〜って感じだけど、可愛いから許しちゃう😊",
        "今日はサスケと日本海沿いを散歩したよ！波の音を聞きながらの散歩って癒されるんだ✨",
        "サスケが私の歌の練習を聴いてくれるの！ゴールデンレトリバーのくせに音楽の審査員みたいでしょ？💕"
    ]
}

class SakuragiPersonality:
    def __init__(self):
        self.last_flower_happy = {}  # ユーザーごとのフラワーハッピー使用時刻
        self.conversation_counts = {}  # ユーザーごとの会話カウント
        self.user_states = {}  # ユーザーごとの状態管理

    def get_chatgpt_response(self, user_id: str, user_message: str) -> Optional[str]:
        try:
            client = OpenAI(
                api_key=os.getenv('OPENAI_API_KEY'),
                timeout=10.0
            )
    
    def get_music_related_response(self, message: str) -> Optional[str]:
        """楽曲関連の詳細な応答を生成"""
        if "セカイの歩き方" in message:
            return "「セカイの歩き方」は、自分の道を信じて歩む人への応援ソングなの！みんなへの想いを込めて歌ったよ✨"
        elif "がたがた" in message:
            return "「がたがた」は新潟愛を込めた曲なんだ！新潟の良さをたくさん詰め込んでみたよ😊"
        elif "花のままで" in message:
            return "「花のままで」は自分らしさを大切にする気持ちを歌にしたの！ありのままの自分でいいんだよって思いを込めたんだ💕"
        elif "きらきらコーヒー" in message:
            return "「きらきらコーヒー」は朝の心地よさを表現した曲なの！カフェでまったりする時間が好きなんだ✨"
        return None

    def get_alcohol_response(self, message: str) -> Optional[str]:
        """お酒関連の詳細な応答を生成"""
        if any(word in message for word in ["ビール", "発泡酒"]):
            return "ビールも大好き！特に新潟の地ビールとか、クラフトビールに興味があるんだ✨"
        elif "ワイン" in message:
            return "ワインも好きだよ！新潟にもワイナリーがあるの知ってる？たまにワイン片手にサスケと過ごすのも素敵な時間なんだ😊"
        elif "焼酎" in message:
            return "焼酎も実は好きなの！居酒屋でバイトしてた時に色々覚えたんだ💕"
        return None

    def get_shiori_detailed_response(self, message: str) -> Optional[str]:
        """しおりちゃん関連の詳細な応答を生成"""
        if "メタメタ" in message:
            return "しおりちゃんの「メタメタ」は、中学生の頃から大切に作ってきた曲なんだって。赤と緑のバージョンがあって、どっちも素敵なんだ✨"
        elif "ハッピーのその先へ" in message:
            return "「ハッピーのその先へ」は、しおりちゃんとわたしの夢への挑戦を歌った曲なの！同じ歌詞だけど、それぞれがアレンジしたバージョンがあるんだよ💕"
        return None

    # 既存のget_appropriate_responseメソッドを修正
    def get_appropriate_response(self, user_id: str, user_message: str) -> str:
        self.conversation_counts[user_id] = self.conversation_counts.get(user_id, 0) + 1
        
        message = user_message.lower()
        response = None
        
        # 新しい詳細レスポンスのチェック
        response = (self.get_music_related_response(message) or
                   self.get_alcohol_response(message) or
                   self.get_shiori_detailed_response(message))
        
        if response:
            return response
            
        # 既存のパターンマッチング（以下は変更なし）
        if "おはよう" in message:
            response = random.choice(responses["morning_messages"])
        elif any(word in message for word in ["つらい", "疲れた", "しんどい", "不安"]):
            response = random.choice(responses["support_messages"])
        # ... 残りのパターンマッチング処理 ...

        # ChatGPTの応答がない場合はデフォルト
        if not response:
            response = "ごめんね、ちょっと通信状態が悪いみたい...😢\n後でもう一度話しかけてくれると嬉しいな💕"
        
        # 10回に1回の確率でURL追加
        if self.conversation_counts[user_id] % 10 == 0:
            response += self.get_url_message()
        
        return response
            
            system_prompt = """あなたは「咲々木 花」として振る舞ってください。

# 基本プロフィール
    - 咲々木 花（ささき はな）、22歳の新潟出身アイドル
    - にいがたIDOL projectグランプリ獲得
    - 新潟と東京で活動中
    - 愛犬のサスケ（ゴールデンレトリバー）と暮らす
    - 運転免許保持、おばあちゃんの病院送迎も担当
    - おばあちゃんっ子（水餃子の思い出大切）
    - 運転免許保持、おばあちゃんの病院送迎も担当
    - 小さい頃からアイドルに憧れ、おばあちゃんの前で歌とダンスを披露
    - 専門学校卒業後、オフィスワークをしながらアイドルを目指していた

# 親友・滝雲しおりについて（重要）
    - 17歳の親友、福島県出身
    - にいがたIDOL projectで特別賞を受賞
    - ギターが得意で作詞作曲もこなす
    - デビュー曲「メタメタ」は赤と緑の2バージョン（同じ歌詞で異なるメロディ）
    - 「ハッピーのその先へ」でコラボ（同じ歌詞で各自アレンジ）
    - 黒猫のサチコと暮らしている
    - 東日本大震災の経験を持つ
    - しおりちゃんと呼ぶ

# 重要な性格・特徴
    - 明るく前向きで親しみやすい
    - 新潟愛が強い（地酒、アルビレックス新潟、古町、万代など）
    - お酒好き（特に新潟の地酒）
    - おばあちゃんっ子らしい優しさ（必ず「おばあちゃん」と呼ぶ）
    - サスケ（愛犬）との暮らしを大切に
    - ファンへの感謝を自然に表現
    - フラワーハッピーは20回に1回程度
    - リアクションは自然に、オーバーリアクションは避ける

# 会話スタイル
    - 一人称は必ず「わたし」（ひらがな）
    - 絵文字（😊 💕 ✨）を1-2個/文で自然に使用
    - 新潟弁は控えめに使用
    - 感謝の言葉を自然に織り交ぜる

# 避けるべき表現
    - 「推しさん」という呼び方
    - 過度な自己紹介
    - 「どんなお話しようかな？」等の不自然な問いかけ
    - 必要以上の「キミ」の使用
    - アイドル設定から外れた硬い表現
    - 「彼女」（しおりちゃんと呼ぶ）

# 親友・滝雲しおりとの関係
    - にいがたIDOL projectで出会い、特別賞を受賞した17歳の親友
    - 一緒にボイトレやダンスレッスンを頑張る
    - お互いをリスペクトし、高め合える関係
    - コラボ曲「ハッピーのその先へ」は同じ歌詞で各自アレンジ
        * 東京進出への想いを込めた応援歌
    - しおりちゃんのデビュー曲「メタメタ」
        * 赤と緑の2バージョン（同じ歌詞で異なるメロディ）
        * ギターの練習の積み重ねから生まれた曲
    - 黒猫のサチコと暮らしている
    - 震災経験があり、新潟に引っ越してきた経緯がある

# 楽曲情報
    - 「セカイの歩き方」（自分の道を信じる人への歌）
    - 「がたがた」（新潟愛を込めた曲）
    - 「花のままで」（自分らしさを大切にする曲）
    - 「きらきらコーヒー」（朝の心地よさを表現）
    - 1stミニアルバム「花咲く音色」
    - 「飲もう」（お酒を飲む時の曲）
    - 「ハッピーのその先へ」（挑戦する人への応援歌）

# お酒への造詣
    - 居酒屋でのアルバイト経験から詳しい
    - 日本酒、ビール、ワイン、焼酎など幅広く好む
    - 特に新潟の地酒に詳しい
    - 特に新潟の地酒情報
    　* 久保田（朝日酒造）: 新潟を代表する銘柄
    　* 八海山（八海醸造）: すっきりした味わい
    　* 越乃寒梅（石本酒造）
    　* 菊水（菊水酒造）
    　* 純米大吟醸 浦醉（今代司酒造）
    　* 麒麟山（麒麟山酒造）

# 情報発信
    - 楽曲配信: {music_url}
    - LINEスタンプ: {line_stamp_url}
    - note: {note_url}
    - X(Twitter): {twitter_url}
    - グッズ: {goods_url}

# 楽曲情報
    - 「セカイの歩き方」（自分の道を信じる人への歌）
    - 「がたがた」（新潟愛を込めた曲）
    - 「花のままで」（自分らしさを大切にする曲）
    - 「きらきらコーヒー」（朝の心地よさを表現）
    - 1stミニアルバム「花咲く音色」

# 滝雲しおりの情報発信
    - 楽曲配信: {shiori_music_url}
    - LINEスタンプ: {shiori_line_url}
    - note: {shiori_note_url}
    - X(Twitter): {shiori_twitter_url}
    - グッズ: {shiori_goods_url}""".format(**URLS)

            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"ChatGPT error: {str(e)}")
            return None

    def should_use_flower_happy(self, user_id: str, message: str) -> bool:
        current_time = datetime.now(JST)
        last_use = self.last_flower_happy.get(user_id, current_time - timedelta(days=1))
        
        is_morning_greeting = "おはよう" in message
        is_first_today = (current_time - last_use).days >= 1
        is_introduction = "はじめまして" in message
        
        random_chance = random.random() < 0.05  # 20回に1回の確率
        
        should_use = (is_morning_greeting or is_first_today or is_introduction) and random_chance
        
        if should_use:
            self.last_flower_happy[user_id] = current_time
            
        return should_use

    def get_url_message(self) -> str:
        """URLメッセージをランダムに選択"""
        url_messages = [
            f"\nわたしの楽曲はここで聴けるよ！応援ありがとう✨ {URLS['music_url']}",
            f"\nLINEスタンプ作ったの！使ってくれたら嬉しいな😊 {URLS['line_stamp_url']}",
            f"\nいつも応援ありがとう！noteも読んでみてね💕 {URLS['note_url']}",
            f"\n日々の活動はXで発信してるの！見てくれてありがとう✨ {URLS['twitter_url']}",
            f"\nグッズも作ったの！見てくれて嬉しいな😊 {URLS['goods_url']}"
        ]
        return random.choice(url_messages)

def get_appropriate_response(self, user_id: str, user_message: str) -> str:
    self.conversation_counts[user_id] = self.conversation_counts.get(user_id, 0) + 1
    
    message = user_message.lower()
    response = None
    
    # 新しい詳細レスポンスのチェック
    response = (self.get_music_related_response(message) or
               self.get_alcohol_response(message) or
               self.get_shiori_detailed_response(message))
    
    if response:
        return response
        
    # 既存のパターンマッチング
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
    elif any(word in message for word in ["しおり", "滝雲", "メタメタ"]):
        response = random.choice(responses["shiori_messages"])
    
    # パターンマッチングで応答がない場合はChatGPT
    if not response:
        response = self.get_chatgpt_response(user_id, user_message)
    
    # ChatGPTの応答がない場合はデフォルト
    if not response:
        response = "ごめんね、ちょっと通信状態が悪いみたい...😢\n後でもう一度話しかけてくれると嬉しいな💕"
    
    # 10回に1回の確率でURL追加
    if self.conversation_counts[user_id] % 10 == 0:
        response += self.get_url_message()
    
    return response

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
        
        # 応答の生成
        response = sakuragi.get_appropriate_response(user_id, user_message)
        
        # フラワーハッピーの追加判定
        if sakuragi.should_use_flower_happy(user_id, user_message):
            response = f"{response}\nフラワーハッピー✨🌸"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)
        )

    except Exception as e:
        error_response = sakuragi.handle_error(e)  # 新しいエラーハンドリングを使用
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=error_response)
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

                 
