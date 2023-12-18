'''
from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}





'''
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
app = FastAPI()
################################################################
from hugchat import hugchat
from hugchat.login import Login
import os, time
email = os.getenv("HUGGING_ID")
passwd = os.getenv("HUGGING_PASSWORD")
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET")) 
class HuggingChat:  
    def __init__(self):
        self.sign = Login(email, passwd)
        self.cookies = self.sign.login()
        self.chatbot = hugchat.ChatBot(cookies=self.cookies.get_dict())
        self.conversation = self.chatbot.new_conversation(2)

    def get_response(self, user_input):
        response = self.chatbot.chat(
	            text=user_input,
                _stream_yield_all=True,
                conversation=self.conversation,
        )
        return response
hugging_chat = HuggingChat()
# Line Bot config
@app.get("/")
async def root():
    return {"message": "Hello World"}
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
@app.post("/callback")
async def callback(request: Request):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Missing Parameters")
    return "OK"
@handler.add(MessageEvent, message=TextMessage)
def handling_message(event):
    if isinstance(event.message, TextMessage):
        quick_reply=QuickReply(items=
            [
                QuickReplyButton(action=MessageAction(label=f'我還在思考{profile.display_name}的問題中，點擊我回答您的問題', text=f'{event.source.user_id}')),
            ]
        )
        start_time = time.time()
        profile = line_bot_api.get_profile(event.source.user_id)
        if event.message.text == event.source.user_id:
            if file_exists(f'{event.source.user_id}.txt'):
                with open(file_path, 'r') as file:
                    file_content = file.read()
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=file_content))
                os.remove(f'{event.source.user_id}.txt')
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請再等一下，我還在思考您的問題', quick_reply = quick_reply))
            return
        user_message = event.message.text
        reply_msg = hugging_chat.get_response(user_message)
        total_text = ""
        for resp in reply_msg:
            elapsed_time = time.time() - start_time
            if resp['type'] == 'stream':
                total_text = f"{total_text}{resp['token']}"
            if elapsed_time > 3:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text='請再等一下，我還在思考您的問題', quick_reply = quick_reply))
        if elapsed_time <= 3:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=total_text))
        else:
            with open(f'{event.source.user_id}.txt', 'w') as file:
                file.write(total_text)
