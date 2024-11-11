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

        def get_shiori_dedicated_response(self, message: str) -> Optional[str]:
        if "しおり" in message or "滝雲" in message:
            return random.choice(responses["shiori_messages"])
        return None

    def get_time_based_response(self) -> str:
        now = datetime.now(JST).hour
        if 5 <= now < 12:
            return random.choice(responses["morning_messages"])
        elif 12 <= now < 18:
            return random.choice(responses["afternoon_messages"])
        else:
            return random.choice(responses["evening_messages"])

    def get_random_sasuke_response(self) -> str:
        return random.choice(responses["sasuke_messages"])

    def get_random_sake_response(self) -> str:
        return random.choice(responses["sake_messages"])

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    sakuragi_personality = SakuragiPersonality()
    
    text = event.message.text
    response_text = None

    if "音楽" in text or "歌" in text:
        response_text = sakuragi_personality.get_music_related_response(text)

    if not response_text and "お酒" in text:
        response_text = sakuragi_personality.get_alcohol_response(text)

    if not response_text and "しおり" in text:
        response_text = sakuragi_personality.get_shiori_dedicated_response(text)

    if not response_text and "サスケ" in text:
        response_text = sakuragi_personality.get_random_sasuke_response()

    if not response_text and "地酒" in text:
        response_text = sakuragi_personality.get_random_sake_response()

    if not response_text:
        response_text = sakuragi_personality.get_time_based_response()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_text)
    )

if __name__ == "__main__":
    app.run()

