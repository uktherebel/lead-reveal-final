from dotenv import load_dotenv
from langchain import hub 
from langchain.agents import (
  AgentExecutor, 
  create_react_agent,
  create_structured_chat_agent,
)
from langchain_core.tools import Tool
from langchain_ollama import ChatOllama
from langchain.memory.buffer import ConversationBufferMemory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

load_dotenv()

model = ChatOllama(
  model='qwen2.5-coder:7b', 
  base_url='http://localhost:11434'
)

def get_current_time(*arg, **kwargs): 
  """
  Returns the current time in H:MM AM/PM
  """
  import datetime
  now = datetime.datetime.now()
  return now.strftime('%I:%M %p')

def search_wikipedia(query):
  """Searches wikipedia and returns the summary of the first result"""
  from wikipedia import summary 

  try: 
    return summary(query, sentence=2)
  except: 
    return "I couldn't find any information on that."
  
tools = [
  Tool(
    name='Time', 
    func=get_current_time,
    description='Useful for when you need to know the current time'
  ), 
  Tool(
    name='Wikipedia', 
    func=search_wikipedia,
    description='Useful for when you need to know information about a topic'
  ),
]

prompt = hub.pull("hwchase17/structured-chat-agent")

memory = ConversationBufferMemory(
  memory_key='chat_history', return_messages=True
)

agent = create_structured_chat_agent(llm=model, tools=tools, prompt=prompt)

agent_executor = AgentExecutor.from_agent_and_tools(
  agent=agent,
  tools=tools,
  verbose=True,
  memory=memory,
  handle_parsing_errors=True,
)

initial_message = "You are an AI assistant that can provide helpful answers using available tools.\nIf you are unable to answer, you can use the following tools: Time and Wikipedia."

memory.chat_memory.add_message(SystemMessage(content=initial_message))

while True: 
  user_input = input('User: ')
  if user_input == 'exit': 
    break 
  memory.chat_memory.add_message(HumanMessage(content=user_input))

  response = agent_executor.invoke({'input': user_input})
  print('Bot:', response['output'])

  memory.chat_memory.add_message(AIMessage(content=response['output']))