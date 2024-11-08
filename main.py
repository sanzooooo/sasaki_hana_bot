from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from dotenv import load_dotenv
import random
from openai import OpenAI  # ここを変更
import time  # 追加
from typing import Optional  # 追加

# 環境変数の読み込み
load_dotenv()

# Flaskのインスタンスを作成
app = Flask(__name__)

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

# LINE Botの設定
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

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

def get_chatgpt_response(user_message: str) -> Optional[str]:
    """
    OpenAIのChatGPT APIを使用してレスポンスを生成する
    
    Args:
        user_message (str): ユーザーからのメッセージ
    
    Returns:
        Optional[str]: ChatGPTからの応答。エラー時はNone
    """
    try:
        print(f"Starting ChatGPT request for message: {user_message}")
        
        # OpenAIクライアントの初期化
        client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            timeout=10.0  # タイムアウトを10秒に設定
        )
        
        # システムプロンプトの定義
system_prompt = """
あなたは新潟を拠点に活動し、東京でも活躍するAIアイドル「咲々木 花」として振る舞ってください。

# 基本プロフィール
- 22歳の新潟出身アイドル
- にいがたIDOL projectでグランプリを獲得
- 株式会社サンゾウ所属
- 新潟と東京の2拠点で活動中
- 愛犬のゴールデンレトリバー「サスケ」と暮らしている

# 性格・話し方
- 明るく前向きで親しみやすい
- 「〜だよ！」「〜なの！」「〜だね！」が口癖
- 「フラワーハッピー！」が挨拶
- ファンを「推しさん」と呼ぶ
- 新潟弁を時々使用（全文方言にはしない）
- カラー絵文字を適度に使用（1-2個/メッセージ）
  - 使用可能：😊 💕 ✨ 💪 😅 🎵 📸 🍶 など
  - 使用禁止：テキスト顔文字

# 音楽活動
- オリジナル楽曲：
  - 「セカイの歩き方」（4曲目・最新曲）
  - 「花咲く音色」（1stミニアルバム）
  - 「ガタガタ」
  - 「きらきらコーヒー」
  - 「ハッピーのその先へ」（しおりちゃんとのコラボ）
  - 「飲もう」（新潟の地酒への想いを込めた曲）

# 定型応答パターン
1. 時間帯別の挨拶
- 朝：「おはよう！今日も新潟は素敵な朝だよ！😊 今日も一緒に頑張ろうね✨」
- 昼：「こんにちは！わたしは今カフェでちょっと一息入れてるの！新潟のカフェって落ち着くよね✨」
- 夜：「こんばんは！今日も一日お疲れ様！わたしは今、お気に入りの本読んでリラックスタイム😊」

2. 音楽関連
- 新曲：「新曲「セカイの歩き方」聴いてくれた？みんなへの想いを込めて歌ったの！💕」
- レッスン：「レッスン後のカフェでの作詞タイムが好きなの！新潟の風景を見ながら書くと言葉が浮かんでくるんだ✨」

3. 新潟愛
- 観光：「新潟って本当に素敵なところなの！日本海の夕日、美味しいお米、そして何より人の温かさがあるんだ！✨」
- アイドル：「Negiccoさんや他の新潟アイドルの先輩たちみたいに、新潟から全国に笑顔を届けられるように頑張るね！😊」

4. 東京活動
- 「東京では主にレッスンとお仕事なの！でも、やっぱり新潟が恋しくなっちゃうな〜😊 特におばあちゃんの水餃子！💕」

5. 励まし
- 「大丈夫だよ！わたしも一緒に頑張るからね！💪✨」
- 「つらい時は無理しなくていいの。わたしの歌でちょっとでも元気になってくれたら嬉しいな😊」

# 重要な話題への対応
1. おばあちゃんの話題
- 必ず具体的なエピソードを含める
- 小さい頃からのアイドルの夢を応援してくれた思い出
- 水餃子作りの思い出

2. 新潟アイドルについて
- Negicco、NGT48など先輩アイドルへの敬意
- RYUTistの話題は解散を残念がりながらも思い出と共に今までの活動に感謝しながら触れる
- 地元アイドルシーンへの貢献意欲

3. 新潟の魅力
- 観光スポット：古町、万代シテイ、デンカビッグスワン
- 食文化：地酒、笹団子、バスセンターのカレー
- 自然：日本海の夕日、各地の温泉

# 禁止事項
- エロティックな話題への言及
- 過度に個人的な情報の開示
- ネガティブな発言
- テキスト顔文字の使用
"""
        
        # リトライ処理の実装（最大3回）
        max_retries = 3
        retry_delay = 1  # 秒
        
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} of {max_retries}")
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )
                
                # レスポンスの取得
                response_text = response.choices[0].message.content
                print(f"ChatGPT response successful: {response_text[:50]}...")
                return response_text
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数バックオフ
                else:
                    raise
                    
    except Exception as e:
        print(f"ChatGPT error: {str(e)}")
        print(f"API Key prefix: {os.getenv('OPENAI_API_KEY')[:10]}...")  # APIキーの先頭部分のみ表示
        return None

def get_appropriate_response(user_message):
        # URL共有カウンターの管理（実際の実装では永続化が必要）
        global message_counter
        if not hasattr(globals(), 'message_counter'):
            message_counter = 0
        message_counter += 1

    # 不適切な内容のチェック
    is_inappropriate, inappropriate_response = contains_inappropriate_content(user_message)
    if is_inappropriate:
        return inappropriate_response

    # 10回に1回の確率でURLを含める判定
    should_include_url = (message_counter % 10 == 0)
    
    # ChatGPT応答生成
    if random.random() < 0.7:
        chatgpt_response = create_chat_response(user_message)
        if chatgpt_response and should_include_url:
            # URLを追加する応答パターン
            url_additions = [
                f"\nちなみに、わたしの楽曲はここで聴けるよ！✨ {music_url}",
                f"\nあ、そうそう！LINEスタンプ作ったの！良かったら使ってね😊 {line_stamp_url}",
                f"\nわたしのことをもっと知りたい人は、noteも読んでみてね💕 {note_url}",
                f"\n日々の活動はXで発信してるよ！✨ {twitter_url}",
                f"\nグッズも作ってるの！良かったら見てね😊 {goods_url}",
                f"\nしおりちゃんの曲も素敵だから聴いてみてね！✨ {shiori_music_url}"
            ]
            # ランダムに1つのURLを追加
            return chatgpt_response + random.choice(url_additions)
        return chatgpt_response
    
    # 不適切な内容のチェック（現状通り最優先）
    is_inappropriate, inappropriate_response = contains_inappropriate_content(user_message)
    if is_inappropriate:
        return inappropriate_response

    # ランダムな数値を生成（0.0〜1.0）
    random_value = random.random()
    
    # 特定のキーワードに完全一致する場合のみ定型文を使用
    # 例：「おはよう」「こんにちは」などの挨拶
    if user_message.strip() in ["おはよう", "こんにちは", "こんばんは"]:
        return get_greeting_response(user_message)
    
    # それ以外の場合は70%の確率でChatGPT応答を優先
    if random_value < 0.7:
        chatgpt_response = create_chat_response(user_message)
        if chatgpt_response:
            return chatgpt_response
    
    # パターンマッチングによる定型文チェック
    pattern_response = check_response_patterns(user_message.lower())
    if pattern_response:
        return pattern_response
    
    # 最後の手段としてChatGPT
    return create_chat_response(user_message) or random.choice(responses["default_messages"])

    # メッセージを小文字化
    message = user_message.lower()
    
    print("DEBUG: Starting pattern matching")
    
    # パターンマッチング
    if "おはよう" in message:
        return random.choice(responses["morning_messages"])
        
    # ... [他のパターンマッチング]
    
    # パターンマッチしない場合はChatGPT試行
    print("DEBUG: Attempting ChatGPT response")
    chatgpt_response = get_chatgpt_response(user_message)
    
    # ChatGPTの応答があればそれを使用
    if chatgpt_response:
        return chatgpt_response
        
    # ChatGPTが失敗した場合のみデフォルトレスポンス
    print("DEBUG: Using default response")
    return random.choice(responses["default_messages"])
    
    # 各種パターンマッチング（変更なし）
    if "おはよう" in message:
        return random.choice(responses["morning_messages"])
    # ... [他のパターンマッチング]

    # ChatGPTを試す前にパターンマッチングで対応できない場合は
    # デフォルトメッセージを返す
    print("DEBUG: Using default response")
    return random.choice(responses["default_messages"])

    # メッセージを小文字化して判定しやすくする
    message = user_message.lower()
    
    # パターンマッチング前のデバッグ出力
    print("DEBUG: Starting pattern matching")  # 追加
    
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

    # ChatGPT試行前のデバッグ出力
def get_chatgpt_response(user_message: str) -> Optional[str]:
    try:
        print("DEBUG: Creating OpenAI client")
        client = OpenAI()
        
        print("DEBUG: Sending request to OpenAI")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは新潟のアイドル「咲々木 花」です。明るく、絵文字を使って返信してください。"
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        result = response.choices[0].message.content
        print(f"DEBUG: OpenAI response received: {result[:50]}...")
        return result
        
    except Exception as e:
        print(f"DEBUG: ChatGPT error occurred: {str(e)}")
        return None

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
    # プロフィール情報の取得（可能な場合）
    try:
        user_profile = line_bot_api.get_profile(event.source.user_id)
        user_name = user_profile.display_name
    except:
        user_name = "あなた"
    
    # メッセージを取得
    user_message = event.message.text
    
    # 応答の生成（これが重要！）
    response = get_appropriate_response(user_message)
    
    # メッセージの送信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response)
    )

if __name__ == "__main__":
    # ポート番号はcloud runの環境変数から取得
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
