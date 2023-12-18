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
from linebot.models import MessageEvent, TextMessage, TextSendMessage, QuickReply, QuickReplyButton, MessageAction
app = FastAPI()
################################################################
from hugchat import hugchat
from hugchat.login import Login
import os, time, threading
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
def process_message(user_message,total_text,user_id,event):
    reply_msg = hugging_chat.get_response(user_message)
    for resp in reply_msg:
        if resp['type'] == 'stream':
            total_text[0] = f"{total_text[0]}{resp['token']}"
    event.set()
    with open(f'/tmp/{user_id}.txt', 'w') as file:
        file.write(total_text[0])
    
@handler.add(MessageEvent, message=TextMessage)
def handling_message(event):
    if isinstance(event.message, TextMessage):
        start_time = time.time()
        profile = line_bot_api.get_profile(event.source.user_id)
        quick_reply=QuickReply(items=
            [
                QuickReplyButton(action=MessageAction(label='點擊我，詢問我想好了沒', text=f'{event.source.user_id}')),
            ]
        )
        if event.message.text == event.source.user_id:
            if os.path.exists(f'/tmp/{event.source.user_id}.txt'):
                with open(f'/tmp/{event.source.user_id}.txt', 'r') as file:
                    file_content = file.read()
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=file_content))
                os.remove(f'/tmp/{event.source.user_id}.txt')
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'請再等等\n我還在思考{profile.display_name}的問題中', quick_reply = quick_reply))
            return
        user_message = event.message.text
        total_text = [""]
        completion_event = threading.Event()
        worker = threading.Thread(target=process_message, args=(user_message, total_text, event.source.user_id, completion_event))
        worker.start()
        if completion_event.wait(timeout=3):
            new_text=total_text[0]
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=total_text))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f'請再等等\n我還在思考{profile.display_name}的問題中', quick_reply = quick_reply))
