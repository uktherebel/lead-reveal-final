from langchain_ollama.llms import OllamaLLM
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from google.cloud import firestore
from langchain_google_firestore import FirestoreChatMessageHistory


PROJECT_ID = 'xai-chatbot-30176', 

COLLECTION_NAME = 'chat_history'
SESSION_ID = 'user_session_new'

print('Initialising Firestore Client...')
client = firestore.Client(project='xai-chatbot-30176')

print("Initialising Firestore Chat Message History...")
chat_history = FirestoreChatMessageHistory(
  session_id=SESSION_ID, 
  collection=COLLECTION_NAME,
  client=client
)
print("Chat history initialised.")
print("Curent chat history:", chat_history.messages)

llm = ChatOllama(
  model='qwen2.5-coder:7b', 
  base_url="http://localhost:11434", 
)

messages = [
  (
    'system', 
    'You are a helpful assistant that translates English to French. Translate the user sentence.'
  ), 
  ("user", "I love programming."),
]

# .invoke 
ai_msg = llm.invoke(messages)
ai_msg
print(ai_msg)

# chat_history = []
# AIMessage - conversing with the chatbot 
# This is the message history

# system_message = SystemMessage(content='You are a pedantic teacher who teaches every concept involved.') 

# chat_history.append(system_message)
messages = [
  SystemMessage(content='Solve the following math problems'),
  HumanMessage(content='What is 81 divided by 9'), 
  AIMessage(content='81 divided by 9 is 9.'), 
  HumanMessage(content='Alright, repeat the same question I asked before.')
]

# result = llm.invoke(messages)
# print(result.content)

while True: 
  query = input("You: ")
  if query.lower() == 'exit': 
    break 
  # chat_history.append(HumanMessage(content=query))
  chat_history.add_user_message(query)

  result = llm.invoke(chat_history.messages)
  # response = result.content
  # chat_history.append(AIMessage(content=response))
  chat_history.add_ai_message(result)

  print(f"AI: {result.content}")

print(chat_history)