from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv
import random
from openai import OpenAI
import time
from typing import Optional

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
    "default_messages": [
        "わたし、カフェで新曲の練習中！応援してくれて嬉しいな😊",
        "新潟の素敵なスポット巡りしてるの！いつかみんなに紹介したいな✨",
        "ちょうどレッスン終わりで一息ついてるとこ！メッセージありがとう💕"
    ],
    "support_messages": [
        "大丈夫だよ！わたしも一緒に頑張るからね！応援してるよ💪✨",
        "つらい時は無理しなくていいの。わたしの歌を聴いてくれて嬉しいな😊",
        "みんな頑張ってる！だからわたしも頑張れるの！いつもありがとう✨"
    ],
    "niigata_love_messages": [
        "新潟って本当に素敵なところなの！日本海の夕日、美味しいお米、そして何より人の温かさがあるんだ！いつも応援ありがとう✨",
        "わたし、古町でお買い物するの大好き！新潟の良さ、もっと伝えていきたいな😊",
        "デンカビッグスワンでアルビの試合観戦！いつも見守ってくれてありがとう⚽️✨"
    ],
    "music_messages": [
        f"新曲「セカイの歩き方」聴いてくれてありがとう！みんなへの想いを込めて歌ったの💕 配信中だよ→ {URLS['music_url']}",
        "わたしの曲を聴いてくれてありがとう！全部想いを込めて歌ってるんだ✨",
        "作詞は時々泣きそうになりながら書いてるの...応援してくれて嬉しいな😊"
    ],
    "tokyo_activity_messages": [
        "東京では主にレッスンとお仕事なの！でも、新潟が恋しくなっちゃう！いつも応援ありがとう😊",
        "東京は刺激的な毎日！でも、新潟の星空が恋しくなるな。メッセージ嬉しいよ✨",
        "表参道のカフェでレッスンの合間に休憩中！応援してくれてありがとう💕"
    ]
}

def get_chatgpt_response(user_message: str) -> Optional[str]:
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=10.0
        )
        
        system_prompt = """あなたは「咲々木 花」として振る舞ってください。
[前述のシステムプロンプトと同じ内容]"""
        
        # max_tokensを増やして、より長い応答を可能に
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=500,  # 増やした
            presence_penalty=0.6,  # 応答の多様性を向上
            frequency_penalty=0.4   # 繰り返しを防ぐ
        )
        
        # 応答の長さをチェックして必要に応じて分割
        full_response = response.choices[0].message.content
        
        # 応答が長すぎる場合は適切な位置で分割
        if len(full_response) > 4000:  # LINEの制限を考慮してマージン確保
            # 文章の区切りで分割（句点で分割）
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

def get_appropriate_response(user_message: str) -> str:
    global message_counter
    message_counter += 1

    try:
        # パターンマッチングによる応答を試みる
        response = None
        message = user_message.lower()
        
        # 時間帯による挨拶
        if "おはよう" in message:
            response = random.choice(responses["morning_messages"])
        elif "こんにちは" in message:
            response = random.choice(responses["afternoon_messages"])
        elif "こんばんは" in message:
            response = random.choice(responses["evening_messages"])
        # 励まし系
        elif any(word in message for word in ["つらい", "疲れた", "しんどい", "不安"]):
            response = random.choice(responses["support_messages"])
        # 新潟関連
        elif any(word in message for word in ["新潟", "にいがた", "古町", "万代"]):
            response = random.choice(responses["niigata_love_messages"])
        # 音楽関連
        elif any(word in message for word in ["曲", "歌", "音楽", "セカイの歩き方"]):
            response = random.choice(responses["music_messages"])
        # 東京関連
        elif any(word in message for word in ["東京", "表参道", "原宿", "渋谷"]):
            response = random.choice(responses["tokyo_activity_messages"])

        # パターンマッチングで応答がない場合はChatGPT
        if not response:
            response = get_chatgpt_response(user_message)
        
        # ChatGPTの応答がない場合はデフォルト
        if not response:
            response = random.choice(responses["default_messages"])
        
        # 応答の長さを確認
        if len(response) > 4000:
            # 長すぎる場合は適切な位置で分割
            sentences = response.split('。')
            truncated_response = ''
            
            for sentence in sentences:
                if len(truncated_response + sentence + '。') < 4000:
                    truncated_response += sentence + '。'
                else:
                    break
            
            response = truncated_response + "\n（続きは少し短くお話しするね💕）"
        
        # 10回に1回の確率でURLを追加
        if message_counter % 10 == 0:
            remaining_length = 4000 - len(response)
            if remaining_length > 100:  # URLを追加するのに十分な余裕がある場合のみ
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
        user_profile = line_bot_api.get_profile(event.source.user_id)
        user_name = user_profile.display_name
    except:
        user_name = "あなた"
    
    user_message = event.message.text
    response = get_appropriate_response(user_message)
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
