from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = YLewHmcR3Obqe7tQFowCLhIdd8ahNrhQmV1QWD67W7pohNplru4LtXyg/MUtUcXva89FfisL706HefagS7Tmnf+fxSscuqmoLi7qpgDmjDl0Jx5URkq5IFQBeVUmiw8B06xU+wQX4e/q2i9swsDdQQdB04t89/1O/w1cDnyilFU=
handler = bec56562d5ce4583e42307887c94fd40

# Webhookからのリクエストを処理するエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    # リクエストヘッダーから署名検証のための値を取得
    signature = request.headers['X-Line-Signature']
    
    # リクエストボディを取得
    body = request.get_data(as_text=True)
    
    try:
        # 署名を検証し、問題なければhandleに定義されている関数を呼び出す
        handler.handle(body, signature)
    except InvalidSignatureError:
        # 署名検証で失敗した場合は例外をあげる
        abort(400)
    
    return 'OK'

# メッセージイベントを処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # オウム返しする
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))

if __name__ == "__main__":
    # ポート番号はcloud runの環境変数から取得
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
