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

# 設定
ADMIN_ID = "U0cf263ba9e075fcac42d60e20bd950c3"  # 管理者のID（文字列）

ALLOWED_USERS = {
    "U0cf263ba9e075fcac42d60e20bd950c3",  # 管理者のID
}  # 集合（set）として定義

BLOCKED_USERS = set()  # 空の集合

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
    "short_messages": [
        "うん！✨",
        "そうなの！💕",
        "分かったよ！😊",
        "オッケー✨",
        "その通り！💕",
        "了解！😊"
    ],
    "sake_messages": [
        "最近の一押しは八海山の純米大吟醸！すっきりした味わいがたまらないの✨",
        "久保田の千寿って知ってる？新潟を代表する地酒の一つなんだよ！😊",
        "今代司酒造さんの浦醉が大好き。蔵開きにも行ったことあるんだ💕",
        "越乃寒梅の白ラベルは、すっきりした飲み口で女性に人気なの！わたしも大好きなお酒の一つなんだ✨",
        "麒麟山の辛口は、お刺身との相性が抜群！新潟の地酒って本当に美味しいよね😊",
        "菊水の辛口は、冷やでも熱燗でも美味しいの！季節によって楽しみ方を変えるのが好きなんだ💕",
        "〆張鶴の花まるは、優しい味わいで飲みやすいんだ！お酒初心者の方にもおすすめだよ✨",
        "鶴齢の純米酒、すっきりしてるのに深みがあって素敵なの！地元の居酒屋さんで見つけたお気に入りなんだ😊",
        "笑四季酒造の「干支」シリーズ、毎年楽しみにしてるの！限定酒って特別感があって好きなんだ💕",
        "村祐の無濾過生原酒、お燗にするととっても美味しいの！冬は特におすすめだよ✨",
        "越路乃紅梅の純米吟醸、フルーティーな香りが魅力的なんだ！女子会でも人気なの😊",
        "萬寿鏡の「かたふね」、新潟を代表する辛口酒の一つなんだ！お刺身との相性バツグンだよ💕",
        "雪中梅の純米酒、すっきりとした中にも旨みがあって、つい飲みすぎちゃうの！でも、ほどほどにね✨",
        "稲川酒造の「想天坊」も大好き！蔵元さんの想いが詰まったお酒って素敵だよね😊",
        "真野鶴の純米大吟醸、佐渡島の美味しい地酒なの！キレのある味わいがたまらないんだ💕"
    ],
    "niigata_food_messages": [
        "新潟の枝豆は「茶豆」って呼ばれてて、香り高くて本当に美味しいの！夏の日本酒のおともに最高なんだ✨",
        "のどぐろは新潟の高級魚として有名なの！脂がのっていて、炭火焼きにすると絶品なんだよ💕",
        "笹団子は新潟の伝統的なお菓子なの！おばあちゃんが作ってくれるの、すっごく美味しいんだ😊",
        "新潟のお米はコシヒカリが有名だけど、萬寿（まんじゅ）や瑞穂（みずほ）も絶品なの！お米の味の違いがわかるようになったんだ✨",
        "へぎそばって独特の食感があるの！つなぎにフノリっていう海藻を使ってるから、ツルツルしてるんだ💕",
        "新潟の寒ブリは脂がのっててとっても美味しいの！おばあちゃんが煮付けにしてくれるのが大好きなんだ😊",
        "あとね、新潟はナスも有名なの！漬物にすると絶品で、わたしの大好物なんだ✨",
        "イタリア野菜の「バーニャカウダ」も新潟の特産品なの！新鮮な野菜をアンチョビソースで食べるんだ💕",
        "新潟のタラ汁は冬の定番なの！具だくさんで体が温まるんだ。おばあちゃんのタラ汁が一番美味しいよ😊",
        "白根の地域で作られるル レクチエっていう洋梨が絶品なの！新潟の冬の味覚として大人気なんだ✨",
        "新潟のイチゴ「越後姫」って知ってる？甘くて大粒で、わたしの大好物なの💕",
        "雑煮には「わらび」や「なめこ」が入るのが新潟流なの！お正月はおばあちゃんの手作り雑煮が楽しみなんだ😊",
        "新潟の郷土料理「のっぺ」は具沢山の煮物なの！冬は特においしくて、体が温まるんだ✨",
        "菊の花のてんぷらも新潟の伝統料理なの！秋になると食べたくなっちゃうんだ💕"
    ],
    "niigata_specialty_messages": [
        "新潟の魚介類は日本海の荒波で育つから、身が引き締まっていて美味しいの！佐渡沖でとれる寒ブリは絶品なんだ✨",
        "村上の「塩引き鮭」って知ってる？伝統的な製法で作られる新潟の冬の味覚なの！お土産にも人気なんだ💕",
        "新潟のお米は日本一！コシヒカリはもちろん、新之助や萬寿（まんじゅ）も絶品なの😊",
        "笹団子は季節によって中身が変わるの！夏はこしあん、冬はつぶあんが多いんだ✨ わたしは両方大好き！",
        "新潟のおやつといえば「ぽっぽ焼き」！駅で買って帰るのが定番なの💕",
        "油揚げの具材をたっぷり詰めた「いなり巻き」も新潟の郷土料理なの！おばあちゃんが作ってくれるのが大好きなんだ😊"
    ],
    "niigata_seasonal_food_messages": [
        "春は山菜がいっぱい！タラの芽やこごみ、うどの天ぷらが美味しいの✨",
        "夏は茶豆に始まり茶豆に終わるって感じ！新潟の夏の味覚の王様なんだ💕",
        "秋はル レクチエや新米の季節！新潟の秋は美味しいものばかりなの😊",
        "冬は寒ブリにノドグロ、タラ汁に雑煮！温かい郷土料理が恋しくなる季節なんだ✨"
    ],
    "niigata_transport_messages": [
        "新潟交通のバスは市内の足として活躍してるの！万代シティバスセンターが主要ターミナルなんだ✨",
        "萬代橋ラインって知ってる？新潟駅と古町を結ぶ大切なバス路線なの！わたしもよく利用するんだ💕",
        "BRT（バス高速輸送システム）は新潟の新しい交通手段なの！白山駅から青山までスムーズに移動できるんだ😊",
        "バスでおばあちゃんの病院に行く時は、ICカード「りゅーと」を使ってるの！とっても便利なんだ✨",
        "新潟市内をぐるっと観光するなら、「空港リムジン」や「観光循環バス」がおすすめだよ！主要スポットを巡れるんだ💕"
    ],
    "albirex_messages": [
        "アルビレックス新潟といえばサッカーだけじゃないの！バスケットボールチームもすごく強いんだ✨",
        "アルビレックスBBは市体育館がホームアリーナなの！熱い試合を観に行くのが楽しみなんだ💕",
        "野球のアルビレックスBCは、新潟県内の野球文化を盛り上げてるの！わたしも応援してるんだ😊",
        "デンカビッグスワンでサッカー、シティホールでバスケ、ハードオフエコスタでBCと、アルビレックスファミリーは新潟のスポーツを引っ張ってるんだ✨",
        "アルビレックスは新潟のスポーツ文化の象徴なの！サッカー、バスケ、野球と、それぞれが新潟を代表するチームなんだ💕"
    ],
    "sake_brewery_messages": [
        "新潟の酒蔵って、見学できるところも多いの！今代司酒造さんは古町にあって、歴史ある蔵並みが素敵なんだ✨",
        "朱鷺と暮らす郷の「清酒 朱鷺の里」は、佐渡の自然と共生する想いが込められてるんだ！素敵だよね😊",
        "北雪酒造さんの見学ツアーに行ったことがあるの！酒造りの工程を見るのって勉強になるし楽しいんだ💕",
        "越後武蔵野酒造さんは、酒蔵カフェもあって、地酒ソフトクリームが人気なの！わたしもよく行くんだ✨",
        "樋木酒造さんは、酒蔵見学の後に試飲もできるんだ！新潟の酒造りの歴史を感じられる素敵な場所だよ😊"
    ],
    "sake_pairing_messages": [
        "新潟の地酒は、やっぱり地元の魚との相性が抜群なの！特に寒鰤との組み合わせが好きなんだ✨",
        "夏は冷やした地酒と枝豆を一緒に楽しむのが定番！新潟の枝豆は「茶豆」って呼ばれて特に美味しいんだ💕",
        "熱燗にした地酒と、のっぺい汁って相性バッチリなの！おばあちゃんの作るのっぺい汁が大好きなんだ😊",
        "春は花見酒に新潟の地酒！桜を見ながらの一杯って特別な気分になれるよね✨",
        "寒い季節は温めた地酒と一緒にへぎそばを楽しむのが好きなの！新潟の食文化って本当に素晴らしいよね💕"
    ],
    "niigata_spot_messages": [
        "新潟市の萬代橋は夜景が綺麗なの！わたしもよく写真を撮りに行くんだ✨ 特に夕暮れ時がおすすめだよ！",
        "マリンピア日本海に行ったことある？イルカのショーが可愛いくて、わたしも時々見に行くんだ！海の生き物に癒されるの😊",
        "朱鷺メッセからの夜景がすごく綺麗なの！新潟の街並みが一望できて、デートスポットとしても人気なんだ💕",
        "白山神社は新潟市で一番古い神社なの！おばあちゃんとよくお参りに行くんだ✨ 風情があって素敵な場所だよ",
        "新潟ふるさと村って知ってる？新潟のおいしいものが全部集まってるの！わたしも友達と行くのが大好きなんだ💕",
        "北方文化博物館は豪農の館を利用した博物館なの！庭園が特に素敵で、わたしも写真を撮りに行くことがあるんだ✨",
        "清五郎浜から見る夕日がとっても綺麗！サスケと一緒に散歩するのがお気に入りなの😊",
        "いくとぴあ食花は新潟の食と花のテーマパークなの！季節の花々が綺麗で、カフェごはんも美味しいんだ💕"
    ],
    "niigata_onsen_messages": [
        "月岡温泉って知ってる？美人の湯って呼ばれてて、お肌がすべすべになるんだ！わたしも大好きな温泉の一つなの✨",
        "弥彦温泉からの夕陽がとっても綺麗！弥彦山と日本海が一望できて、最高のロケーションなんだ💕",
        "新潟市内の天然温泉「りゅーとぴあ」は、お仕事帰りにもサッと寄れて便利！わたしもたまに行くんだ😊",
        "岩室温泉は新潟市から近くて、日帰り温泉としても人気なの！お湯がとっても気持ちいいんだ✨",
        "瀬波温泉は日本海を眺めながら入れる温泉なの！波の音を聞きながらの湯浴みが最高に気持ちいいんだ💕",
        "五頭温泉郷は山あいの静かな温泉地なの！紅葉の季節がとっても綺麗で、おばあちゃんとよく行くんだ✨",
        "咲花温泉は阿賀野川沿いにある温泉なの！渓谷美と一緒に楽しめる隠れた名湯だよ😊",
        "村杉温泉はラジウム泉で有名なの！湯治場として昔から愛されてきた温泉なんだ✨"
    ],
    "niigata_nature_messages": [
        "白山公園の桜は本当に綺麗！春になるとお花見を楽しむ人でいっぱいになるの✨ わたしもサスケと散歩するのが大好きなんだ！",
        "五泉のチューリップ畑って知ってる？春になると色とりどりのチューリップが咲き誇って、まるで虹のじゅうたんみたい💕",
        "日和山浜で見る夕日が素敵なの！おばあちゃんと一緒に散歩すると、やっぱり新潟っていいなって感じるんだ😊",
        "日本海の夕日は世界一だと思うな！関屋浜から見る夕日は本当に綺麗で、心が洗われるような気持ちになるの✨",
        "弥彦山の紅葉がとっても綺麗なの！ロープウェイからの眺めは絶景で、新潟の自然の素晴らしさを感じられるんだ💕",
        "福島潟のハスの花を見に行ったことある？夏になると沢山のハスの花が咲いて、とっても綺麗なんだ✨",
        "佐渡島はトキの野生復帰で有名だけど、自然がいっぱいで癒されるの！たまに遊びに行くんだ😊",
        "国営越後丘陵公園は季節の花々が楽しめて、ピクニックにぴったり！わたしもよく友達と行くんだ💕",
        "鳥屋野潟や信濃川沿いの桜をまた見るのが楽しみだな💕"
    ],
    "niigata_food_spot_messages": [
        "古町の老舗お店「江口だんご」さんの団子、おばあちゃんが連れて行ってくれるの！やっぱり美味しいんだ✨",
        "市場通りの「鍋茶屋」さんは新潟の郷土料理が楽しめるの！わたしも友達と行くことがあるんだ💕",
        "万代島鮮魚センターは新鮮な海の幸がいっぱい！わたしもたまに家族と一緒に行くんだ😊",
        "ぽっぽ焼きって知ってる？新潟市民の駅おやつの定番なの！懐かしい味がクセになるんだ✨",
        "イタリアン食堂「MARIA」さんのピザ、実は超人気店なの！新潟の食材をイタリアンで楽しめるんだ💕",
        "寺泊の魚市場は新鮮な魚介類の宝庫！おばあちゃんと一緒に行くと色んな発見があるの😊",
        "醤油おかきで有名な「三幸」の直売所は、お土産選びにぴったり！わたしも友達に配ることあるんだ✨",
        "西安刀削麺の本店は新潟にあるって知ってた？実は全国チェーン展開する前からの名店なの！たまに食べに行くんだ💕"
    ],
    "sasuke_messages": [
        "サスケったら、今日もわたしのレッスンバッグの上で寝てるの！もう、どいてよ〜って感じだけど、可愛いから許しちゃう😊",
        "高校生の頃からずっと一緒のサスケ！日本海沿いの散歩が大好きなんだ✨",
        "サスケが私の歌の練習を聴いてくれるの！ゴールデンレトリバーのくせに音楽の審査員みたいでしょ？💕"
    ],
    "niigata_love_messages": [
        "新潟の素晴らしさを伝えられて嬉しいな！わたしも新潟のことが大好きなの✨",
        "古町も万代も素敵な場所だよね！新潟の街並みって本当に魅力的なんだ💕",
        "新潟の魅力って語り始めたら止まらないの！それだけ素敵な場所なんだ😊"
    ],
    "niigata_festival_messages": [
        "新潟まつりの民謡流しは迫力があって素敵なの！浴衣を着て踊るの、すっごく楽しいんだ✨",
        "長岡まつりの大花火大会は日本有数の規模なの！フェニックスの打ち上げは感動的で、毎年見に行くんだ💕",
        "古町どんどんは新潟の夏の風物詩！おばあちゃんと一緒に行くのが恒例なんだ😊",
        "光のページェント万代は冬の夜を彩るイルミネーションなの！ロマンチックな雰囲気が大好きなんだ✨",
        "にいがた総おどりは市民みんなで踊れるお祭りなの！新潟の踊りの文化を感じられるんだ💕"
    ],
    "niigata_weather_messages": [
        "新潟の雪景色は幻想的なんだ！でも、除雪は大変だから、おばあちゃんの家の雪かきを手伝うようにしてるの✨",
        "新潟の夏は日本海からの風が気持ちいいの！でも湿度が高くて、ちょっと大変な時もあるんだ💕",
        "新潟は日本海側特有の気候なの！冬は雪が多いけど、その分春の桜が特別キレイに感じるんだ😊",
        "新潟の夕焼けは日本海に沈む太陽が絶景なの！特に春と秋はサスケと一緒によく見に行くんだ✨"
    ],
    "niigata_culture_messages": [
        "新潟漆器は江戸時代から続く伝統工芸なの！艶やかな仕上がりが特徴的なんだ✨",
        "村上木彫堆朱も新潟の誇る伝統工芸！繊細な彫刻が施された作品は芸術的なんだ💕",
        "新潟の織物「亀田縞」は丈夫で味わい深いの！昔からの技法が今でも受け継がれてるんだ😊",
        "新潟には方言もたくさんあるの！「おじゃる」とか「～だっちゃ」とか、地域によって違うんだ✨"
    ],
    "niigata_entertainer_messages": [
        "ヒカキンさんは新潟市の出身なの！YouTuberのパイオニアとして世界的に有名になったんだ✨",
        "小林幸子さんは新潟が誇る演歌歌手！デンカビッグスワンでのコンサートは伝説的なんだ💕",
        "柏木由紀さんは新潟市出身のアイドル！AKB48で活躍して、今でも新潟の魅力を発信してくれてるの😊",
        "Superflyの越智志帆さんは新潟市出身なの！力強い歌声で有名なアーティストさんなんだ✨"
    ],
    "niigata_manga_messages": [
        "高橋留美子先生は新潟市出身なの！「うる星やつら」「らんま1/2」「犬夜叉」など、たくさんの名作を生み出してるんだ✨",
        "浦沢直樹先生は新潟市出身の漫画家なの！「MONSTER」や「20世紀少年」で世界的に有名なんだ✨",
        "水島新司先生の「ドカベン」「あぶさん」は野球漫画の金字塔！新潟出身の漫画家さんなんだ💕",
        "魔夜峰央先生も新潟出身なの！「パタリロ！」でお馴染みの大人気漫画家さんなんだ😊",
        "井上きみどり先生は新潟出身で、「おひとりさま出産」など女性の生き方を描く漫画家さんなんだ✨",
        "「弱虫ペダル」の渡辺航先生も新潟出身！自転車競技を題材にした大人気作品を描いてるんだ💕",
        "高橋留美子先生の作品は世界中で愛されてるの！新潟が誇る漫画家さんの一人なんだ💕"
    ],
    "niigata_industry_messages": [
        "新潟の醸造技術は日本酒だけじゃないの！醤油や味噌も全国に誇れる品質なんだ✨",
        "新潟の金属加工技術は世界でも有名なの！特に洋食器は品質が高くて評価されてるんだ💕",
        "米菓製造も新潟の重要な産業なの！おせんべいやあられの種類が豊富で、どれも美味しいんだ😊",
        "新潟の農業技術も素晴らしいの！特にお米の栽培技術は日本一だと思うんだ✨"
    ],
    "niigata_transport_messages": [
        # 既存のメッセージに加えて
        "トキエアは新潟初の地域航空会社なの！新潟と全国を結ぶ翼として期待されてるんだ✨",
        "トキエアの機体にはトキがデザインされてるの！新潟らしさが素敵だよね💕"
    ],
    "sado_messages": [
        "佐渡金山が世界遺産に登録されたの！江戸時代からの歴史ある金山なんだ✨",
        "佐渡には伝統芸能がたくさんあるの！能や人形芝居が今でも受け継がれてるんだ💕",
        "佐渡の自然は本当に素晴らしいの！トキの野生復帰も成功して、環境保護のモデルケースになってるんだ😊",
        "佐渡の海の幸は絶品！特に寒ブリは最高においしいんだ✨"
    ],
    "niigata_idol_messages": [
        "新潟はアイドルの聖地なんだよ！NGT48の劇場は古町にあって、たくさんのファンが全国から来てくれるの✨",
        "にいがたIDOL projectはたくさんの夢を持ったアイドルが集まるオーディションなの！わたしもグランプリを獲らせていただいたんだ💕",
        "Negiccoは新潟を代表するアイドルグループなの！新潟の魅力を全国に発信してくれてる素敵なお姉さんたちなんだ✨",
        "RYUTistも新潟を拠点に活動しているアイドルグループなの！新潟の良さを歌に込めて発信してるんだ💕",
        "新潟からデビューしたアーティストはたくさんいるの！みんなが新潟の音楽シーンを盛り上げてくれてるんだ😊",
        "古町界隈にはライブハウスがたくさんあって、いつも素敵な音楽で溢れてるの！わたしも大好きな場所なんだ✨",
        "しおりちゃんもにいがたIDOL projectで特別賞を獲ったの！新潟には才能あふれるアイドルがたくさんいるんだ😊"
    ]
    "support_messages": [
        "そんなときは、ゆっくり休むのも大切だよ！わたしも応援してるからね✨",
        "頑張り屋さんなあなたをいつも見守ってるよ！一緒に前を向いて進もうね💕",
        "大丈夫、きっと良いことあるはず！わたしも精一杯応援してるからね😊"
    ],
}

# system_promptをクラスの外に移動
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
    - 時には「うん！」「そうなの！」などの短い返答も

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
                        max_tokens=250,
                        presence_penalty=0.6,
                        frequency_penalty=0.2
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

        # 30%の確率でChatGPTに直接振る
        if random.random() < 0.3:
            chat_response = self.get_chatgpt_response(user_id, user_message)
            if chat_response:
                return chat_response
        
        # 名前の呼び方を最初にチェック（最優先）
        if any(name in message for name in ["咲々木 花", "咲々木花", "咲々木", "花さん", "花ちゃん"]):
            return random.choice([
                "はーい！わたしのこと呼んでくれたの？嬉しいな✨",
                "わたしのこと呼んでくれてありがとう！何かお話ししたいことある？💕",
                "はいはーい！咲々木 花だよ！いつも応援ありがとう😊"
            ])
            
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
        elif any(word in message for word in ["観光", "スポット", "名所", "見どころ", "観光地"]):
            response = random.choice(responses["niigata_spot_messages"])
        elif any(word in message for word in ["温泉", "湯", "スパ", "温泉街", "湯治"]):
            response = random.choice(responses["niigata_onsen_messages"])
        elif any(word in message for word in ["自然", "公園", "景色", "夕日", "桜", "紅葉"]):
            response = random.choice(responses["niigata_nature_messages"])
        elif any(word in message for word in ["酒蔵", "蔵元", "見学"]):
            response = random.choice(responses["sake_brewery_messages"])
        elif any(word in message for word in ["枝豆", "茶豆", "のどぐろ", "笹団子", "へぎそば", "おにぎり", "米", "魚"]):
            response = random.choice(responses["niigata_food_messages"])
        elif any(word in message for word in ["名産", "特産", "銘産", "名物"]):
            response = random.choice(responses["niigata_specialty_messages"])
        elif any(word in message for word in ["旬", "季節", "時期"]):
            response = random.choice(responses["niigata_seasonal_food_messages"])
        elif any(word in message for word in ["おつまみ", "肴", "つまみ", "一緒に飲む", "酔う","酔った", "飲み屋"]):
            response = random.choice(responses["sake_pairing_messages"])
        elif any(word in message for word in ["バス", "新潟交通", "りゅーと", "BRT", "交通"]):
            response = random.choice(responses["niigata_transport_messages"])
        elif any(word in message for word in ["アルビ", "アルビレックス", "バスケ", "野球", "スポーツ"]):
            response = random.choice(responses["albirex_messages"])
        elif any(word in message for word in ["アイドル", "ライブ", "idol", "IDOL", "音楽シーン", "NGT", "ネギッコ"]):
            response = random.choice(responses["niigata_idol_messages"])
        elif any(word in message for word in ["祭り", "まつり", "イベント", "花火"]):
            response = random.choice(responses["niigata_festival_messages"])
        elif any(word in message for word in ["天気", "気候", "雪", "暑い", "寒い"]):
            response = random.choice(responses["niigata_weather_messages"])
        elif any(word in message for word in ["工芸", "伝統", "文化", "方言"]):
            response = random.choice(responses["niigata_culture_messages"])
        elif any(word in message for word in ["芸能人", "有名人", "歌手", "アーティスト", "ヒカキン", "YouTuber"]):
            response = random.choice(responses["niigata_entertainer_messages"])
        elif any(word in message for word in ["漫画", "まんが", "マンガ", "漫画家"]):
            response = random.choice(responses["niigata_manga_messages"])
        elif any(word in message for word in ["産業", "技術", "製造", "工場"]):
            response = random.choice(responses["niigata_industry_messages"])
        elif any(word in message for word in ["飛行機", "航空", "トキエア", "空港"]):
            response = random.choice(responses["tokiair_messages"])
        elif any(word in message for word in ["佐渡", "金山", "世界遺産", "島"]):
            response = random.choice(responses["sado_messages"])
        elif any(word in message for word in ["グルメ", "食べ物", "レストラン", "食事", "ご飯", "ランチ"]):
            response = random.choice(responses["niigata_food_spot_messages"])

        # ここに短い返答の処理を追加
        if not response and random.random() < 0.2:
            response = random.choice(responses["short_messages"])
        
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

        # 誰でもIDを確認できる特別コマンド
        if user_message == "myid":
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"あなたのユーザーID: {user_id}")
            )
            return

        # 管理者用コマンド
        if user_id == ADMIN_ID:
            if user_message == "show_id":
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"あなたのユーザーID: {user_id}")
                )
                return
            elif user_message.startswith("check_id:"):
                # 他のユーザーのIDを確認するコマンド
                target_id = user_message.split(":")[1].strip()
                try:
                    profile = line_bot_api.get_profile(target_id)
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f"ユーザー情報:\nID: {profile.user_id}\n名前: {profile.display_name}")
                    )
                except Exception as e:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="指定されたIDのユーザーは見つかりませんでした。")
                    )
                return

        # ブロックされたユーザーのチェック
        if user_id in BLOCKED_USERS:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="申し訳ありません。このアカウントはご利用いただけません。")
            )
            return
            
        if len(ALLOWED_USERS) > 0 and user_id not in ALLOWED_USERS:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="サービスを利用するには、まず 'myid' と送信してIDを確認し、X（旧Twitter）のDMにてIDを伝えてください✨")
            )
            return
            
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
