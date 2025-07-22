from typing import Annotated
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse 
import os, json
from .ai.openai import OpenAIWrapper
from .ai.qwen import Qwen
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict
from typing import List
import numpy as np 
# import ollama
from .pydantic.base import ChatRequest, ChatResponse
from .pydantic.lead_and_reveal import PlanItem, PlanResponse, LeadAndRevealRequest, LeadAndRevealResponse
from datetime import datetime
from .llm_config import create_code_chain
load_dotenv()

# --- App Initialization ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"])

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <label>Item ID: <input type="text" id="itemId" autocomplete="off" value="foo"/></label>
            <label>Token: <input type="text" id="token" autocomplete="off" value="some-key-token"/></label>
            <button onclick="connect(event)">Connect</button>
            <hr>
            <label>Message: <input type="text" id="messageText" autocomplete="off"/></label>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
        var ws = null;
            function connect(event) {
                var itemId = document.getElementById("itemId")
                var token = document.getElementById("token")
                ws = new WebSocket("ws://localhost:8000/items/" + itemId.value + "/ws?token=" + token.value);
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                event.preventDefault()
            }
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""

# --- AI Configuration ---
def load_system_prompt(): 
   try: 
      with open('src/prompts/teacher.md', 'r') as f: 
         return f.read()

   except FileNotFoundError: 
      return None 
   
system_prompt = load_system_prompt()
openai_api_key = os.getenv("OPENAI_API_KEY")
qwen_api_key = os.getenv('QWEN_API_KEY')

if not qwen_api_key: 
   raise ValueError('QWEN_API_KEY environment variable not set.')

ai_platform = Qwen(
   api_key=qwen_api_key, 
   # system_prompt=system_prompt
)

# --- API Endpoints ---
@app.get("/")
async def root():
    return {"message": "API is running"}

@app.post('/generate')
async def generate_code(task: str): 
    llm, prompt_template = create_code_chain()
    result = llm.invoke(
        prompt_template.invoke(
            {
                'task': task
            }
        )
    )
    return {'code': result.content}
    

@app.get('/')
async def get(): 
    return HTMLResponse(html)

async def get_cookie_or_token(
        websocket: WebSocket, 
        session: Annotated[str | None, Cookie()] = None, 
        # from Cookie(), retrieve the parameter 'session' and convert it to str (if not already str), else set to None 
        token: Annotated[str | None, Query()] = None
): 
    if session is None and token is None: 
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    return session or token


@app.websocket('/items/{item_id}/ws')
async def websocket_endpoint(
    *, 
    websocket: WebSocket, 
    item_id: str, 
    q: int | None = None, 
    cookie_or_token: Annotated[str, Depends(get_cookie_or_token)],
): 
    await websocket.accept()
    while True: 
        data = await websocket.receive_text()
        await websocket.send_text(
            f"Session cookie or query token value is {cookie_or_token}"
        )
        if q is not None: 
            await websocket.send_text(f"Query parameter q is: {q}")
        await websocket.send_text(f"Message text was: {data}, for item ID: {item_id}")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = ai_platform.chat(request.prompt)
    return ChatResponse(
      explanation = result
    )

@app.post("/lead-and-reveal", response_model=LeadAndRevealResponse)
async def lead_and_reveal(request: LeadAndRevealRequest):
    if request.answer:
        # 2. If answer is provided, evaluate it
        evaluation = ai_platform.evaluate_answer(request.code_solution, request.answer)
        return LeadAndRevealResponse(question="", evaluation=evaluation)
    else:
        # 1. If no answer, generate a question
        question = ai_platform.lead_and_reveal(request.code_solution)
        return LeadAndRevealResponse(question=question)


ai_platform1 = OpenAIWrapper(api_key=openai_api_key)

@app.post('/event_identifier')
async def get_event_details(request: ChatRequest):
    result = ai_platform1.chat(request.prompt)
    return result

@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket): 
    await websocket.accept()
    while True: 
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")



# @app.post('/chat', response_model=ChatResponse)
# async def chat(request: ChatRequest): 
#    response_text = '...'
#    return ChatResponse(response=response_text)

# # CPU-bound things - no downtime 
# # shouldn't be async
# @app.get('/calculation')
# def calculation(): 
#    # do some heavy calc 
#    pass 
#    return result 


# @api.get('/getdata')
# async def get_data_from_db():
#    await # request
#    pass 
#    return ""



# GET, POST, PUT, DELETE

# POST - creating a resource 
# PUT - changing a resource 