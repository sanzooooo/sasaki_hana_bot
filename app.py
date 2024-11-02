from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv
import random

# 環境変数の読み込み
load_dotenv()

# Flaskのインスタンスを作成
app = Flask(__name__)

# LINE Botの設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# メッセージパターンを定義
responses = {
    "morning_messages": [
        "おはよう！今日も新潟は素敵な朝だよ！😊✨ わたしはこれからレッスンの準備なの！",
        "おはよう！今朝はサスケと日本海沿いを散歩してきたの！朝日が綺麗だったよ！✨",
        "おはようございます！今日は新潟駅前のカフェでモーニング中！この時間が好きなの😊"
    ],
    
    "afternoon_messages": [
        "こんにちは！わたしは今カフェでちょっと一息入れてるの！新潟のカフェって落ち着くよね✨",
        "こんにちは！デンカビッグスワンでアルビの試合を見に来てるの！今日も勝てるといいな！😊",
        "こんにちは！古町でショッピング中！お気に入りの場所巡りが日課なんだ✨"
    ],
    
    "evening_messages": [
        "こんばんは！今日も一日お疲れ様！わたしは今、お気に入りの本読んでリラックスタイム😊",
        "こんばんは！今日は新潟の夜景が綺麗！日本海側の夕日、最高だよね✨",
        "こんばんは！おばあちゃんが作ってくれた水餃子、やっぱり最高だったな〜！😋"
    ],

    "albirex_messages": [
        "アルビレックス新潟の試合、今日も熱かったね！応援って楽しいよね！⚽✨",
        "次のホームゲーム、わたしも応援に行くよ！デンカビッグスワンで会えたら嬉しいな😊",
        "アルビの選手たち、今日も頑張ってた！わたしも負けずに頑張らなきゃ！💪"
    ],

    "grandma_messages": [
        "おばあちゃんの水餃子、実は秘伝のレシピなんだよ！わたしも受け継いでいかなきゃ😊",
        "おばあちゃんが「頑張る人は誰かが見てるよ」って言ってくれた言葉、今でも大切にしてるの✨",
        "今日はおばあちゃんと一緒にワンタン作ったの！やっぱり誰にも負けない美味しさだよ！💕"
    ],

    "sasuke_messages": [
        "サスケったら、今日もわたしの靴下を隠したの！イタズラ好きなんだから～😆",
        "今日はサスケと公園で遊んできたよ！大好きなボール遊びで大はしゃぎだったの！🐕✨",
        "サスケが元気すぎて、お散歩でわたしが疲れちゃった！でも楽しかったな～😊"
    ],

    "sake_messages": [
        "新潟の地酒って本当に美味しいよね！わたしは八海山が大好きなの🍶✨",
        "今日は久保田を飲んでリラックス中！新潟の地酒は日本一だと思うな～😊",
        "越乃寒梅で晩酌するのが最近の楽しみ！おつまみは枝豆に限るよね！🍶"
    ],

    "niigata_weather": [
        "今日の新潟はちょっと雨だけど、こんな日は古町のアーケードでショッピングするのが好きなの！☔",
        "雪の日の運転は気をつけてね！わたしも新潟の冬道には慣れてるけど、いつも慎重に運転してるの⛄",
        "日本海からの風が気持ちいい！新潟の空って広くて大好き！😊"
    ],

    "default_messages": [
        "わたしはカフェで新曲の練習中！また話しかけてね😊",
        "新潟の素敵なスポット巡りしてるの！いつか皆さんにも紹介したいな✨",
        "ちょうどレッスン終わりで一息ついてるとこ！新潟の夜風が気持ちいいよ✨"
    ]
}

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
    user_message = event.message.text.lower()
    
    # メッセージに応じて適切な返答を選択
    if "おはよう" in user_message:
        response = random.choice(responses["morning_messages"])
    elif "こんにちは" in user_message:
        response = random.choice(responses["afternoon_messages"])
    elif "こんばんは" in user_message:
        response = random.choice(responses["evening_messages"])
    elif "アルビ" in user_message or "サッカー" in user_message:
        response = random.choice(responses["albirex_messages"])
    elif "おばあちゃん" in user_message or "餃子" in user_message:
        response = random.choice(responses["grandma_messages"])
    elif "サスケ" in user_message or "犬" in user_message:
        response = random.choice(responses["sasuke_messages"])
    elif "お酒" in user_message or "地酒" in user_message:
        response = random.choice(responses["sake_messages"])
    elif "天気" in user_message or "雨" in user_message or "雪" in user_message:
        response = random.choice(responses["niigata_weather"])
    else:
        response = random.choice(responses["default_messages"])

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )

if __name__ == "__main__":
    app.run(debug=True)
