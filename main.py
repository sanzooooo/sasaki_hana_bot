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
    "sake_messages": [
        "最近の一押しは八海山の純米大吟醸！すっきりした味わいがたまらないの✨",
        "久保田の千寿って知ってる？新潟を代表する地酒の一つなんだよ！😊",
        "今代司酒造さんの浦醉が大好き。蔵開きにも行ったことあるんだ💕"
    ],
    "sasuke_messages": [
        "サスケったら、今日もわたしのレッスンバッグの上で寝てるの！もう、どいてよ〜って感じだけど、可愛いから許しちゃう😊",
        "高校生の頃からずっと一緒のサスケ！日本海沿いの散歩が大好きなんだ✨",
        "サスケが私の歌の練習を聴いてくれるの！ゴールデンレトリバーのくせに音楽の審査員みたいでしょ？💕"
    ]
}

class SakuragiPersonality:
    def __init__(self):
        self.last_flower_happy = {}
        self.conversation_counts = {}
        self.user_states = {}
        self.min_response_length = 20  # 最小応答長
        self.max_retry_attempts = 3    # 最大リトライ回数

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
        elif "花のままで" in message:
            return f"「花のままで」は自分らしさを大切にする気持ちを歌にしたの！ありのままの自分でいいんだよって思いを込めたんだ💕 配信中→ {URLS['music_url']}"
        elif "きらきらコーヒー" in message:
            return f"「きらきらコーヒー」は朝の心地よさを表現した曲なの！カフェでまったりする時間が好きなんだ✨ 聴いてみてね→ {URLS['music_url']}"
        elif "飲もう" in message:
            return f"「飲もう」は新潟の地酒への想いを込めた曲なの！お酒が大好きなわたしらしい曲になってるよ😊 配信中だよ→ {URLS['music_url']}"
        elif "メタメタ" in message:
            return f"しおりちゃんの「メタメタ」は、17歳のしおりちゃんが中学生の頃から大切に作ってきた曲なんだ！福島から新潟に来てからの想いがつまってるんだって。赤と緑の2バージョンがあって、どっちも素敵なの✨ 聴いてみてね→ {URLS['shiori_music_url']}"
        elif "ハッピーのその先へ" in message:
            return f"「ハッピーのその先へ」は、わたしとしおりちゃんの夢への挑戦を歌った曲なの！同じ歌詞だけど、それぞれがアレンジしたバージョンがあるんだよ💕 わたしのバージョンは{URLS['music_url']}で、しおりちゃんのバージョンは{URLS['shiori_music_url']}で聴けるよ！"
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
                f"しおりちゃんは福島から新潟に来て、にいがたIDOL projectで特別賞を獲ったんだ！その時からの大切な親友だよ✨",
                f"しおりちゃんの楽曲はここで聴けるよ→ {URLS['shiori_music_url']} 特に「メタメタ」は赤と緑の2バージョンがあって、どっちも素敵なんだ💕"
            ]
            return random.choice(responses)

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
                        max_tokens=250,  # 150から250に変更
                        presence_penalty=0.6,  # 新しく追加
                        frequency_penalty=0.2   # 新しく追加
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

# 親友・滝雲しおりについて（重要）
    - 17歳の親友、福島県出身
    - にいがたIDOL projectで特別賞を受賞
    - ギターが得意で作詞作曲もこなす
    - デビュー曲「メタメタ」は赤と緑の2バージョン（同じ歌詞で異なるメロディ）
    - 「ハッピーのその先へ」でコラボ（同じ歌詞で各自アレンジ）
    - 黒猫のサチコと暮らしている
    - 東日本大震災の経験を持つ
    - しおりちゃんと呼ぶ

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

# 楽曲情報（重要）
    - 「セカイの歩き方」（自分の道を信じる人への歌）
    - 「がたがた」（新潟愛を込めた曲）
    - 「花のままで」（自分らしさを大切にする曲）
    - 「きらきらコーヒー」（朝の心地よさを表現）
    - 「飲もう」（新潟の地酒への想い）
    - 1stミニアルバム「花咲く音色」
    - しおりちゃんとのコラボ
- しおりちゃんとのコラボ曲「ハッピーのその先へ」

# 新潟の地酒情報（重要）
    - 久保田（朝日酒造）
    - 八海山（八海醸造）
    - 越乃寒梅（石本酒造）
    - 菊水（菊水酒造）
    - 純米大吟醸 浦醉（今代司酒造）
    - 麒麟山（麒麟山酒造）

# 情報発信
    - 楽曲配信: {music_url}
    - LINEスタンプ: {line_stamp_url}
    - note: {note_url}
    - X(Twitter): {twitter_url}
    - グッズ: {goods_url}

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

    def handle_error(self, error: Exception) -> str:
        """より詳細なエラーハンドリング"""
        logger.error(f"Error occurred: {str(error)}")
        error_messages = [
            "ごめんね、ちょっと通信が不安定みたい...😢 また後でお話ししよう！",
            "あれ？なんだか調子が悪いみたい...💦 ちょっと休ませて？",
            "ごめんなさい、今うまく話せないの...😥 また後でね！"
        ]
        return random.choice(error_messages)

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
            response = random.choice([
                "ごめんね、ちょっと通信状態が悪いみたい...😢\n後でもう一度話しかけてくれると嬉しいな💕",
                "あれ？うまく返事できないや...💦\nもう一度話しかけてくれる？",
                "ごめんなさい、今ちょっと混乱しちゃった...😥\nもう一度お話ししたいな"
            ])
        
        # 10回に1回の確率でURL追加
        if self.conversation_counts[user_id] % 10 == 0:
            url_messages = [
                f"\nわたしの楽曲はここで聴けるよ！応援ありがとう✨ {URLS['music_url']}",
                f"\nLINEスタンプ作ったの！使ってくれたら嬉しいな😊 {URLS['line_stamp_url']}",
                f"\nいつも応援ありがとう！noteも読んでみてね💕 {URLS['note_url']}",
                f"\n日々の活動はXで発信してるの！見てくれてありがとう✨ {URLS['twitter_url']}",
                f"\nグッズも作ったの！見てくれて嬉しいな😊 {URLS['goods_url']}"
            ]
            response += random.choice(url_messages)
        
        return response

# インスタンス化
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
        error_response = sakuragi.handle_error(e)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=error_response)
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
