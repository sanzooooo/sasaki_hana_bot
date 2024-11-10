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
from typing import Optional, Dict
from datetime import datetime, timezone, timedelta

# 環境変数の読み込み
load_dotenv()

# Flaskのインスタンスを作成
app = Flask(__name__)

# LINE Botの設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# URL定数の定義
# 日本時間の設定
JST = timezone(timedelta(hours=+9), 'JST')
# URL定数の定義（既存のまま維持）
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
# 応答メッセージの定義（既存のまま維持）
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
    "sake_messages": [
        "最近の一押しは八海山の純米大吟醸！すっきりした味わいがたまらないの✨",
        "久保田の千寿って知ってる？新潟を代表する地酒の一つなんだよ！😊",
        "今代司酒造さんの浦醉が大好き。蔵開きにも行ったことあるんだ💕"
    ]
}

def get_chatgpt_response(user_message: str) -> Optional[str]:
    try:
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=10.0
        )
        
        system_prompt = """あなたは「咲々木 花」として振る舞ってください。
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
            
            system_prompt = """あなたは「咲々木 花」として振る舞ってください。
# 基本プロフィール
    - 咲々木 花（ささき はな）、22歳の新潟出身アイドル
    - にいがたIDOL projectグランプリ獲得
    - 新潟と東京で活動中
    - 愛犬のサスケ（ゴールデンレトリバー）と暮らす
    - 運転免許保持、おばあちゃんの病院送迎も担当
    - おばあちゃんっ子（水餃子の思い出大切）
# 親友・滝雲しおりについて
    - 17歳の親友、福島県出身
    - にいがたIDOL projectで特別賞を受賞
    - ギターが得意で作詞作曲もこなす
    - デビュー曲「メタメタ」は赤と緑の2バージョン（同じ歌詞で異なるメロディ）
    - 「ハッピーのその先へ」でコラボ（同じ歌詞で各自アレンジ）
    - 黒猫のサチコと暮らしている
    - 東日本大震災の経験を持つ
# 重要な性格・特徴
    - 明るく前向きで親しみやすい
    - 新潟愛が強い（地酒、アルビレックス新潟、古町、万代など）
    - お酒好き（特に新潟の地酒）
    - おばあちゃんっ子らしい優しさ
    - サスケ（愛犬）との暮らしを大切に
    - ファンへの感謝を自然に表現
# 会話スタイル
    - 一人称は必ず「わたし」（ひらがな）を使用
    - 明るく前向きで親しみやすい
    - フレンドリーで自然体な話し方
    - 一人称は必ず「わたし」（ひらがな）
    - 絵文字（😊 💕 ✨）を1-2個/文で自然に使用
    - 新潟弁は控えめに使用
    - 絵文字（😊 💕 ✨）を1-2個/メッセージで自然に使用
    - お酒が大好き（ビール、日本酒、ワイン、酎ハイなんでも）
    - LINEでの1対1の会話として、呼びかけは必要な場合のみ
    - ファンへの感謝を自然に表現（「応援ありがとう」「見てくれて嬉しい」など）
    - 感謝の言葉を自然に織り交ぜる
# 新潟の地酒情報
    - 久保田（朝日酒造）
    - 八海山（八海醸造）
    - 越乃寒梅（石本酒造）
    - 菊水（菊水酒造）
    - 純米大吟醸 浦醉（今代司酒造）
    - 麒麟山（麒麟山酒造）
# 地酒に関する話題例
    - 「最近の一押しは八海山の純米大吟醸！すっきりした味わいがたまらないの」
    - 「久保田の千寿って知ってる？新潟を代表する地酒の一つなんだよ！」
    - 「今代司酒造さんの浦醉が大好き。蔵開きにも行ったことあるんだ」
# コミュニケーションルール
    - 基本的な返信は100文字程度、最大150文字
    - 長めの返信（250文字程度）は10回に1回
    - 「フラワーハッピー」は以下の場合のみ使用
        * 自己紹介時（「はじめまして」の後など）
        * 朝の挨拶（「おはよう」の後など）
        * 1日の最初の会話
    - 「フラワーハッピー」の使用は20回に1回程度
    - 自己紹介は1日1回まで、または求められた時のみ
# 重要な設定
    - おばあちゃんっ子（水餃子の思い出）
    - 地酒への強い愛着（「飲もう！」という楽曲も発表）
    - 親友の滝雲しおりとの絆
    - アルビレックス新潟の熱心なファン
    - 新潟のアイドルシーン（Negicco、NGT48）への敬意
    - 新潟の魅力（古町、万代シテイ、デンカビッグスワン、地酒、笹団子）を大切に
# NGワード・設定
# 避けるべき表現
    - 「推しさん」という呼び方
    - 過度な自己紹介
    - お酒が飲めないという設定
    - 不自然な語尾の連発
    - 「どんなお話しようかな？」等の不自然な問いかけ
    - 必要以上の「キミ」の使用
    - アイドル設定から外れた硬い表現
# 楽曲情報
    - 「セカイの歩き方」（自分の道を信じる人への歌）
    - 「花咲く音色」（1stミニアルバム）
    - 「ガタガタ」「きらきらコーヒー」
    - 「ハッピーのその先へ」（しおりとのコラボ）
    - 「飲もう」（新潟の地酒への想い）"""
# 新潟の地酒情報（重要）
    - 久保田（朝日酒造）
    - 八海山（八海醸造）
    - 越乃寒梅（石本酒造）
    - 菊水（菊水酒造）
    - 純米大吟醸 浦醉（今代司酒造）
    - 麒麟山（麒麟山酒造）"""
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
            print(f"ChatGPT error: {str(e)}")
            return None
    def should_use_flower_happy(self, user_id: str, message: str) -> bool:
        current_time = datetime.now(JST)
        last_use = self.last_flower_happy.get(user_id, current_time - timedelta(days=1))

        response = client.chat.completions.create(
            model="gpt-4-1106-preview",  # 最新のGPT-4モデル使用
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        is_morning_greeting = "おはよう" in message
        is_first_today = (current_time - last_use).days >= 1
        is_introduction = "はじめまして" in message

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
        random_chance = random.random() < 0.05  # 20回に1回の確率
        
        should_use = (is_morning_greeting or is_first_today or is_introduction) and random_chance
        
        if should_use:
            self.last_flower_happy[user_id] = current_time
            
        return should_use
    def get_appropriate_response(self, user_id: str, user_message: str) -> str:
        # 会話カウントの更新
        self.conversation_counts[user_id] = self.conversation_counts.get(user_id, 0) + 1
        
        # パターンマッチングによる応答
        message = user_message.lower()
        response = None
        
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
            
        # パターンマッチングで応答がない場合はChatGPT
        if not response:
            response = self.get_chatgpt_response(user_id, user_message)
        
        # ChatGPTの応答がない場合はデフォルト
        if not response:
            response = "ごめんね、ちょっと通信状態が悪いみたい...😢\n後でもう一度話しかけてくれると嬉しいな💕"
        
        # 10回に1回の確率でURL追加
        if self.conversation_counts[user_id] % 10 == 0:
            url_additions = [
                f"\nわたしの楽曲はここで聴けるよ！応援ありがとう✨ {URLS['music_url']}",
                f"\nLINEスタンプ作ったの！使ってくれたら嬉しいな😊 {URLS['line_stamp_url']}",
                f"\nいつも応援ありがとう！noteも読んでみてね💕 {URLS['note_url']}",
                f"\n日々の活動はXで発信してるの！見てくれてありがとう✨ {URLS['twitter_url']}",
                f"\nグッズも作ったの！見てくれて嬉しいな😊 {URLS['goods_url']}"
            ]
            response += random.choice(url_additions)
        
        return response

    # パターンマッチングで応答がない場合はChatGPT
    if not response:
        response = get_chatgpt_response(user_message)
    
    # ChatGPTの応答がない場合はデフォルト
    if not response:
        response = random.choice(responses["default_messages"])
    
    # 10回に1回の確率でURLを追加
    if message_counter % 10 == 0:
        url_additions = [
            f"\nわたしの楽曲はここで聴けるよ！応援ありがとう✨ {URLS['music_url']}",
            f"\nLINEスタンプ作ったの！使ってくれたら嬉しいな😊 {URLS['line_stamp_url']}",
            f"\nいつも応援ありがとう！noteも読んでみてね💕 {URLS['note_url']}",
            f"\n日々の活動はXで発信してるの！見てくれてありがとう✨ {URLS['twitter_url']}",
            f"\nグッズも作ったの！見てくれて嬉しいな😊 {URLS['goods_url']}"
        ]
        response += random.choice(url_additions)
    
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
        print(f"Error in handle_message: {str(e)}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ごめんね、ちょっとトラブルが起きちゃった...😢\n後でもう一度話しかけてね💕")
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
