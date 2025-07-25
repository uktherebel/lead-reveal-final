from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_core.runnables.base import RunnableLambda, RunnableSequence

load_dotenv()

model = ChatOllama(
  model='qwen2.5-coder:7b', 
  base_url="http://localhost:11434",
)

prompt_template = ChatPromptTemplate.from_messages(
  [
    ('system', 'You are a comedian who tells jokes about {topic}.'), 
    ('human', 'Tell me {joke_count} jokes.')
  ]
)

chain = prompt_template | model | StrOutputParser()

a = ""

if a:
  result = chain.invoke({'topic': 'philosophers', 'joke_count': 6})

  print(result) 

# Create individual runnable sequences (steps in the chain)
format_prompt = RunnableLambda(lambda x: prompt_template.format_prompt(**x))

invoke_model = RunnableLambda(lambda x: model.invoke(x.to_messages()))

parse_output = RunnableLambda(lambda x: x.content)

chain = RunnableSequence(
  first=format_prompt, 
  middle=[invoke_model], 
  last=parse_output
  )

# middle task must be a list 
# if you have 1000 tasks, first as first, 1000th as last, the rest tasks as a list 

if a:
  response = chain.invoke({'topic': 'philosopher', 'joke_count': 5})

  print(response)

# Define additinal processing steps using Runnable Lambdas 

uppercase_output = RunnableLambda(lambda x:x.upper())
count_words = RunnableLambda(lambda x: f"Word count: {len(x.split())}\n{x}")

chain = prompt_template | model | StrOutputParser() | uppercase_output | count_words

result = chain.invoke({
  'topic': 'philosophers', 
  'joke_count': 7,
})

print(result)

# We can use LambdaRunnables to call APIs 