from dotenv import load_dotenv
from langchain import hub 
from langchain.agents import (
  AgentExecutor, 
  create_react_agent,
)
from langchain_core.tools import Tool
from langchain_ollama import ChatOllama

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

tools = [
  Tool(
    name='Time', 
    func=get_current_time, 
    description='Useful for when you need to know the current time',
  )
]

# REACT = Reason and Action
prompt = hub.pull('hwchase17/react')

# this prompt tells llm how to act 

agent = create_react_agent(
  llm=model,
  tools=tools,
  prompt=prompt,
  stop_sequence=True,
)

agent_executor = AgentExecutor.from_agent_and_tools (
  agent=agent, 
  tools=tools, 
  verbose=True 
)

response = agent_executor.invoke({'input': 'What time is it right now?'})

print("response:", response)