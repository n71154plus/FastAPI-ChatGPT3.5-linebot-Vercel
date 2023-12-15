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
import os

email = os.getenv("HUGGING_ID")
passwd = os.getenv("HUGGING_PASSWORD")
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET")) 

class HuggingChat:  
    def __init__(self):
        self.sign = Login(email, passwd)
        self.cookies = self.sign.login()
        self.chatbot = hugchat.ChatBot(cookies=self.cookies.get_dict())
        self.chatbot.delete_all_conversations()
        self.conversation = self.chatbot.new_conversation(2)
        self.chatbot.switch_llm(2)

    def get_response(self, user_input):
        self.chatbot.switch_llm(2)
        response = self.chatbot.chat(
	            text=f"{user_input} 請用中文回答我",
                _stream_yield_all=True,
                conversation=self.conversation,
        )
        response.wait_until_done()
        return response.text

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

        
        user_message = event.message.text


        reply_msg = hugging_chat.get_response(user_message)
        if reply_msg:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_msg))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=user_message))

	    
        



