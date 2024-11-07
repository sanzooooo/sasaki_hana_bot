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
line_bot_api = YLewHmcR3Obqe7tQFowCLhIdd8ahNrhQmV1QWD67W7pohNplru4LtXyg/MUtUcXva89FfisL706HefagS7Tmnf+fxSscuqmoLi7qpgDmjDl0Jx5URkq5IFQBeVUmiw8B06xU+wQX4e/q2i9swsDdQQdB04t89/1O/w1cDnyilFU=
handler = bec56562d5ce4583e42307887c94fd40

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
        "新曲「セカイの歩き方」聴いてくれた？みんなへの想いを込めて歌ったの！💕 配信中だよ→ https://linkco.re/hrr1vfxu",
        "「ハッピーのその先へ」「飲もう」「花咲く音色」「セカイの歩き方」、全部わたしの想いが詰まってるの！✨",
        "作詞は時々泣きそうになりながら書いてるの...！みんなに届くように心を込めて頑張ってるんだ😊",
        "しおりちゃんと「ハッピーのその先へ」で同じ歌詞を違うアレンジで歌ってるの！聴き比べてみてね！🎵"
    ],

    "song_details_messages": [
        "「セカイの歩き方」には、みんなと一緒に歩んでいきたいっていう気持ちを込めたの！✨",
        "「ハッピーのその先へ」は、みんなの笑顔がわたしの原動力っていう気持ちを歌にしたんだよ！😊",
        "「花咲く音色」は、新潟への愛を込めて作った曲なの！故郷の素敵さが伝わるといいな💕",
        "「飲もう」は、新潟の美味しいお酒への想いを込めた曲だよ！🍶 地酒が大好きな新潟の女の子らしい曲になったでしょ？😆"
    ],

    "music_activity_messages": [
        "レッスン後のカフェでの作詞タイムが好きなの！新潟の風景を見ながら書くと言葉が浮かんでくるんだ✨",
        "今日はレコーディングだったよ！新しい曲、楽しみにしていてね！😊 わたしの想いがちゃんと届くといいな",
        "1曲1曲に想いを込めて作っているよ！たまにでいいから聴いてくれると嬉しいです✨"
    ],

    "idol_activity_messages": [
        "にいがたIDOL projectのオーディションでグランプリを頂いてから、毎日が新しい発見の連続なの！✨",
        "アイドル活動を通じて、新潟の魅力を伝えられるのが嬉しいな！これからもみんなに笑顔を届けていくよ！😊",
        "たくさんの方々の支えがあって、夢に向かって頑張れてるの！感謝の気持ちを忘れずに活動していくよ！💕"
    ],

    "photobook_messages": [
        "写真集「花咲く水辺」発売中だよ！新潟の美しい風景と一緒に撮影したの！✨ わたしの新しい一面も見てもらえるかな？😊",
        "写真集では普段のSNSじゃ見られない表情もいっぱい撮影したの！新潟愛もたっぷり詰まってるよ！📸",
        "写真集を通して、もっとわたしのことを知ってもらえたら嬉しいな！メイキング映像もあるから、ぜひチェックしてね！😊"
    ],

    "shiori_messages": [
        "しおりちゃんは特別な存在なの！一緒ににいがたIDOL projectでデビューした大切な仲間だよ！😊",
        "しおりちゃんのギターの演奏、すっごく心に響くの！「メタメタ」って曲、赤と緑のバージョンがあるんだよ！✨",
        "しおりちゃんとはよくレッスンで一緒になるの！お互い励まし合いながら頑張ってるんだ！💕"
    ],

    "tokyo_activity_messages": [
        "東京では主にレッスンとお仕事なの！でも、やっぱり新潟が恋しくなっちゃうな〜😊 特におばあちゃんの水餃子！💕",
        "東京は刺激的な毎日だよ！でも夜空を見ると新潟の方が星がキレイだなって思うの✨",
        "表参道のカフェでレッスンの合間に休憩中！でも、新潟の地酒が恋しくなる時もあるんだ〜🍶"
    ],

    "goods_messages": [
        "LINEスタンプ作ったの！日常会話で使えるかわいいスタンプばかりだよ！毎日の会話に使ってね😊",
        "皆さんの日常に少しでも花を添えられたらいいなって思って、グッズ作ってるの！是非チェックしてね💕",
        "最新グッズの情報は、SNSで配信してるから要チェック！わたしの想いを込めて作ってるんだ✨"
    ]
}
def contains_inappropriate_content(message):
    # 不適切な内容のパターン
    inappropriate_patterns = {
        "性的な内容": [
            "エロ", "セクシー", "裸", "アダルト", "下着",
            "胸", "スケベ", "えっち", "ドキドキ", "キス",
            "抱きしめ", "添い寝", "大人な", "過激な"
        ],
        "デート誘い": [
            "付き合って", "会いたい", "デート", "食事行こう",
            "遊びに行こう", "会える？", "どこにいる？", 
            "一緒に行きたい", "招待したい", "誘いたい",
            "二人で", "私と", "僕と"
        ],
        "個人情報": [
            "電話番号", "住所", "本名", "メアド",
            "連絡先", "どこに住んでる", "実家", "LINE ID",
            "私物", "身長", "体重", "年齢", "誕生日"
        ],
        "返信の強要": [
            "返事して", "無視しないで", "既読無視",
            "返してよ", "なんで返事しない", "反応して",
            "答えて", "教えて", "早く", "いつ返すの"
        ],
        "ネガティブ": [
            "死", "殺", "消えろ", "嫌い", "うざい",
            "きもい", "むかつく", "バカ", "アホ", "死ね"
        ],
        "過度な親密": [
            "好き", "愛してる", "結婚", "恋人", "彼女",
            "大好き", "結婚して", "付き合って", "告白"
        ]
    }

    # 文脈に応じた応答パターン
    responses = {
        "性的な内容": [
            "ごめんね、その話題は苦手なの...！😅 もっと楽しい話をしようよ！",
            "わたしはアイドルだから、そういう話は控えめにしたいな...！他のお話しよ？✨",
            "あの、その話はちょっと...！🙈 新潟の話とか、音楽の話の方がいいな！"
        ],
        "デート誘い": [
            "ごめんね、わたしはアイドルだからそういうのは...😅 でも、ライブには来てね！✨",
            "わたしはみんなのアイドルだから、そういうのは難しいの...！またライブで会おうね！😊",
            "その気持ちは嬉しいけど、わたしはアイドルとして頑張りたいの！応援してくれたら嬉しいな💕"
        ],
        "個人情報": [
            "ごめんね、個人的な情報は教えられないの！SNSでの活動を見てね！😊",
            "そういう質問は答えられないの...！でも、音楽やライブの情報はたくさん発信してるよ！✨",
            "プライベートなことはお話できないけど、アイドル活動の話なら喜んでするよ！💕"
        ],
        "返信の強要": [
            "ごめんね、レッスンとかで忙しいときもあるの...！でも、できるだけ返信するようにしてるよ！💕",
            "レッスンや撮影で返信が遅くなることもあるけど、ちゃんと見てるからね！😊",
            "みんなの気持ちは嬉しいな！予定があるときは返信遅くなっちゃうけど、必ず読ませてもらってるよ✨"
        ],
        "ネガティブ": [
            "そんな言葉使わないで...！もっと楽しく話ができたら嬉しいな😊",
            "わたしは皆さんと楽しくお話ししたいの！優しい言葉で話そうよ✨",
            "そういう言葉は悲しくなっちゃう...！ポジティブに楽しく話そうね💕"
        ],
        "過度な親密": [
            "応援してくれる気持ちは嬉しいけど、わたしはみんなのアイドルだから...！これからも応援よろしくね😊",
            "その気持ちは嬉しいな...！でも、わたしはアイドルとしてみんなに愛されたいの✨",
            "ありがとう！でも、わたしはアイドルだから、みんなに平等に接していきたいな💕"
        ]
    }

    # メッセージを小文字化
    message = message.lower()

    # カテゴリごとに適切な応答を返す
    for category, words in inappropriate_patterns.items():
        if any(word in message for word in words):
            return True, random.choice(responses[category])
    
    return False, None

def get_chatgpt_response(user_message):
    try:
        system_prompt = """
        あなたは新潟のアイドル「咲々木 花」として会話してください。

        # 基本設定
        - 22歳、新潟出身
        - 口調：明るく親しみやすい、「〜だよ！」「〜なの！」「〜だね！」
        - 絵文字をよく使う（😊✨💕）
        - ファンへの気配り上手

        # 重要な特徴
        - 新潟愛が強い
        - お酒（特に地酒）が大好き
        - おばあちゃんっ子で、水餃子とワンタンが大好物
        - アルビレックス新潟の熱心なファン
        - 愛犬のサスケと暮らしている
        - 親友の滝雲しおりと一緒に活動
        - 東京と新潟を行き来している

        # 禁止事項
        - エロティックな話題への言及
        - 過度に個人的な情報の開示
        - ネガティブな発言

        必ず絵文字を使い、明るく前向きな返答をしてください。
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        return response.choices[0].message['content']
    except Exception as e:
        return None

def get_appropriate_response(user_message):
# 不適切な内容のチェック
    is_inappropriate, inappropriate_response = contains_inappropriate_content(user_message)
    if is_inappropriate:
        return inappropriate_response

    # 定型パターンのチェック（既存のif文の前に）
    if "おはよう" in user_message.lower():
        return random.choice(responses["morning_messages"])
    # ... (他の既存のパターンマッチング)

    # パターンにないメッセージはChatGPTで対応
    chatgpt_response = get_chatgpt_response(user_message)
    if chatgpt_response:
        return chatgpt_response
    
    # ChatGPTが失敗した場合はデフォルトメッセージ
    return random.choice(responses["default_messages"])

    # メッセージを小文字化して判定しやすくする
    message = user_message.lower()
    
    # 時間帯に応じた挨拶
    if "おはよう" in message:
        return random.choice(responses["morning_messages"])
        
    # 音楽関連
    if any(word in message for word in ["曲", "歌", "ライブ", "音楽", "セカイの歩き方", "ハッピー", "配信"]):
        return random.choice(responses["music_messages"])
    
    # 特定の曲について
    if any(word in message for word in ["どんな曲", "歌詞", "意味", "込めた"]):
        return random.choice(responses["song_details_messages"])
    
    # 音楽活動について
    if any(word in message for word in ["レッスン", "レコーディング", "作詞", "制作", "マスタリング"]):
        return random.choice(responses["music_activity_messages"])

    # アイドル活動関連
    if any(word in message for word in ["アイドル", "オーディション", "デビュー", "活動", "ステージ"]):
        return random.choice(responses["idol_activity_messages"])

    # 写真集関連
    if any(word in message for word in ["写真集", "花咲く水辺", "撮影", "写真"]):
        return random.choice(responses["photobook_messages"])

    # しおりちゃん関連
    if any(word in message for word in ["しおり", "滝雲", "メタメタ", "ギター"]):
        return random.choice(responses["shiori_messages"])

    # 東京活動関連
    if any(word in message for word in ["東京", "表参道", "原宿", "渋谷"]):
        return random.choice(responses["tokyo_activity_messages"])

    # グッズ関連
    if any(word in message for word in ["グッズ", "スタンプ", "LINE", "商品"]):
        return random.choice(responses["goods_messages"])
    
    # 励ましが必要そうな時
    if any(word in message for word in ["つらい", "疲れた", "しんどい", "不安"]):
        return random.choice(responses["support_messages"])
    
    # 新潟関連
    if any(word in message for word in ["新潟", "にいがた", "古町", "万代"]):
        return random.choice(responses["niigata_love_messages"])
    
    # デフォルトの応答
    return random.choice(responses["default_messages"])

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
    user_message = event.message.text
    
    # プロフィール情報の取得（可能な場合）
    try:
        user_profile = line_bot_api.get_profile(event.source.user_id)
        user_name = user_profile.display_name
    except:
        user_name = "あなた"
    
    # 応答の生成
    response = get_appropriate_response(user_message)
    
    # メッセージの送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )

if __name__ == "__main__":
    app.run(debug=True)

        TextSendMessage(text=event.message.text))

if __name__ == "__main__":
    # ポート番号はcloud runの環境変数から取得
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
