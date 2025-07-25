from dotenv import load_dotenv
from langchain import hub 
from langchain.agents import (
  AgentExecutor, 
  create_tool_calling_agent,
)
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import Tool, StructuredTool
from langchain_ollama import ChatOllama

# Functions for the tools
def greet_user(name: str) -> str:
    """Greets the user by name."""
    return f"Wagwan, {name}!"


def reverse_string(text: str) -> str:
    """Reverses the given string."""
    return text[::-1]


def concatenate_strings(a: str, b: str) -> str:
    """Concatenates two strings."""
    return a + b

# Pydantic Model for tool arguments 
class ConcatenateStringArgs(BaseModel): 
    a: str = Field(description='First string')
    b: str = Field(description='Second string')

tools = [
    Tool(
        name='GreetUser', 
        func=greet_user, 
        description="Greets the user by name.",
    ), 
    Tool(
        name="ReverseString",  # Name of the tool
        func=reverse_string,  # Function to execute
        description="Reverses the given string.",  # Description of the tool
    ),
    StructuredTool.from_function(
        func=concatenate_strings,
        name="ConcatenateStrings",
        description="Concatenates two strings.",
        args_schema=ConcatenateStringArgs, # Schema defining the tool's input arguments
    )
]

model = ChatOllama(model='qwen2.5-coder:7b', base_url='http://localhost:11434') 

prompt = hub.pull("hwchase17/openai-tools-agent")

agent = create_tool_calling_agent(
    llm=model, 
    tools=tools, 
    prompt=prompt, # Prompt template to guide the agent's responses
)

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True, # Handle parsing errors gracefully
)

response = agent_executor.invoke({"input": "Greet Aifer"})
print("Response for 'Greet Alice':", response)

response = agent_executor.invoke({"input": "Reverse the string 'hello'"})
print("Response for 'Reverse the string hello':", response)

response = agent_executor.invoke({"input": "Concatenate 'hello' and 'world'"})
print("Response for 'Concatenate hello and world':", response)