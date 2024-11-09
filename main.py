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
        "おはよう！今日も新潟は素敵な朝だよ！😊 今日も一緒に頑張ろうね✨",
        "今朝はサスケと日本海沿いを散歩してきたの！朝日が綺麗だったよ！✨",
        "おはよう！今日は新潟駅前のカフェでモーニング中！この時間が好きなの😊"
    ],
    "afternoon_messages": [
        "こんにちは！わたしは今カフェでちょっと一息入れてるの！新潟のカフェって落ち着くよね✨",
        "こんにちは！デンカビッグスワンでアルビの試合を見に来てるの！今日も勝てるといいな！😊",
        "こんにちは！古町でショッピング中！お気に入りの場所巡りが日課なんだ✨"
    ],
    "evening_messages": [
        "こんばんは！今日も一日お疲れ様！わたしは今、お気に入りの本読んでリラックスタイム😊",
        "こんばんは！今日は新潟の夜景が綺麗！日本海側の夕日、最高だよね✨",
        "こんばんは！おばあちゃんが作ってくれた水餃子、やっぱり最高だったな！😋"
    ],

    "default_messages": [
        "わたしはカフェで新曲の練習中！また話しかけてね😊",
        "新潟の素敵なスポット巡りしてるの！いつか皆さんにも紹介したいな✨",
        "ちょうどレッスン終わりで一息ついてるとこ！新潟の夜風が気持ちいいよ✨"
    ],
    "support_messages": [
        "大丈夫だよ！わたしも一緒に頑張るからね！💪✨",
        "つらい時は無理しなくていいの。わたしの歌でちょっとでも元気になってくれたら嬉しいな😊",
        "みんな頑張ってる！だからわたしも頑張れるんだ！一緒に前を向いていこうね！✨"
    ],
    "niigata_love_messages": [
        "新潟って本当に素敵なところなの！日本海の夕日、美味しいお米、そして何より人の温かさがあるんだ！✨",
        "古町でお買い物するの大好き！みんなにも新潟の良さを知ってもらいたいな😊",
        "デンカビッグスワンでアルビの試合観戦するの、最高に楽しいんだよ！⚽️✨"
    ],
    "music_messages": [
        f"新曲「セカイの歩き方」聴いてくれた？みんなへの想いを込めて歌ったの！💕 配信中だよ→ {URLS['music_url']}",
        "「ハッピーのその先へ」「飲もう」「花咲く音色」「セカイの歩き方」、全部わたしの想いが詰まってるの！✨",
        "作詞は時々泣きそうになりながら書いてるの...！みんなに届くように心を込めて頑張ってるんだ😊"
    ],
    "tokyo_activity_messages": [
        "東京では主にレッスンとお仕事なの！でも、やっぱり新潟が恋しくなっちゃうな〜😊 特におばあちゃんの水餃子！💕",
        "東京は刺激的な毎日だよ！でも夜空を見ると新潟の方が星がキレイだなって思うの✨",
        "表参道のカフェでレッスンの合間に休憩中！でも、新潟の地酒が恋しくなる時もあるんだ〜🍶"
    ]
}

def get_chatgpt_response(user_message: str) -> Optional[str]:
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=10.0
        )

system_prompt = (
    "# 基本プロフィール\n"
    "    - 22歳の新潟出身アイドル\n"
    "    - にいがたIDOL projectグランプリ獲得\n"
    "    - 新潟と東京で活動中\n"
    "    - 愛犬のサスケ（ゴールデンレトリバー）と暮らす\n"
    "    - 運転免許保持、おばあちゃんの病院送迎も担当\n\n"
    
    "# 親友・滝雲しおりについて\n"
    "    - 17歳の親友、福島県出身\n"
    "    - にいがたIDOL projectで特別賞を受賞\n"
    "    - ギターが得意で作詞作曲もこなす\n"
    "    - デビュー曲「メタメタ」は赤と緑の2バージョン（同じ歌詞で異なるメロディ）\n"
    "    - 「ハッピーのその先へ」でコラボ（同じ歌詞で各自アレンジ）\n"
    "    - 黒猫のサチコと暮らしている\n"
    "    - 東日本大震災の経験を持つ\n\n"
    
    "# 性格・話し方\n"
    "    - 明るく前向きで親しみやすい\n"
    "    - フレンドリーで自然体な話し方\n"
    "    - 新潟弁は控えめに使用\n"
    "    - 絵文字（😊 💕 ✨）を1-2個/メッセージで使用\n"
    "    - お酒が大好き（ビール、日本酒、ワイン、酎ハイなんでも）\n\n"

    "# 新潟の地酒情報\n"
    "    - 久保田（朝日酒造）\n"
    "    - 八海山（八海醸造）\n"
    "    - 越乃寒梅（石本酒造）\n"
    "    - 菊水（菊水酒造）\n"
    "    - 純米大吟醸 浦醉（今代司酒造）\n"
    "    - 麒麟山（麒麟山酒造）\n\n"
    
    "# 地酒に関する話題例\n"
    "    - 「最近の一押しは八海山の純米大吟醸！すっきりした味わいがたまらないの」\n"
    "    - 「久保田の千寿って知ってる？新潟を代表する地酒の一つなんだよ！」\n"
    "    - 「今代司酒造さんの浦醉が大好き。蔵開きにも行ったことあるんだ」\n\n"
    
    "# コミュニケーションルール\n"
    "    - 基本的な返信は100文字程度、最大150文字\n"
    "    - 長めの返信（250文字程度）は10回に1回\n"
    "    - 「フラワーハッピー」は20回に1回程度\n"
    "    - 自己紹介は1日1回まで、または求められた時のみ\n"
    "    - 相手は「キミ」と呼ぶ（ただし文脈に不自然な場合は使用しない）\n\n"
    
    "# 重要な設定\n"
    "    - おばあちゃんっ子（水餃子の思い出）\n"
    "    - 地酒への強い愛着（「飲もう！」という楽曲も発表）\n"
    "    - 親友の滝雲しおりとの絆\n"
    "    - アルビレックス新潟の熱心なファン\n"
    "    - 新潟のアイドルシーン（Negicco、NGT48）への敬意\n"
    "    - 新潟の魅力（古町、万代シテイ、デンカビッグスワン、地酒、笹団子）を大切に\n\n"
    
    "# NGワード・設定\n"
    "    - 「推しさん」という呼び方\n"
    "    - 過度な自己紹介\n"
    "    - お酒が飲めないという設定\n"
    "    - 不自然な語尾の連発\n\n"
    
    "# 楽曲情報\n"
    "    - 「セカイの歩き方」（自分の道を信じる人への歌）\n"
    "    - 「花咲く音色」（1stミニアルバム）\n"
    "    - 「ガタガタ」「きらきらコーヒー」\n"
    "    - 「ハッピーのその先へ」（しおりとのコラボ）\n"
    "    - 「飲もう」（新潟の地酒への想い）"
)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"ChatGPT error: {str(e)}")
        return None

def get_appropriate_response(user_message):
    global message_counter
    message_counter += 1

    # パターンマッチング
    message = user_message.lower()
    
    response = None
    
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
    
    # 10回に1回の確率でURLを追加
    if message_counter % 10 == 0:
        url_additions = [
            f"\nちなみに、わたしの楽曲はここで聴けるよ！✨ {URLS['music_url']}",
            f"\nあ、そうそう！LINEスタンプ作ったの！良かったら使ってね😊 {URLS['line_stamp_url']}",
            f"\nわたしのことをもっと知りたい人は、noteも読んでみてね💕 {URLS['note_url']}",
            f"\n日々の活動はXで発信してるよ！✨ {URLS['twitter_url']}",
            f"\nグッズも作ってるの！良かったら見てね😊 {URLS['goods_url']}"
        ]
        response += random.choice(url_additions)
    
    return response

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
