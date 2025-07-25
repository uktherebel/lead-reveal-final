from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model='gpt-4o')

template = "Tell me a joke about {topic}."
prompt_template = ChatPromptTemplate.from_template(template)

print("----Prompt from Template----")
prompt = prompt_template.invoke({'topic': 'cats'})
# print(prompt)
# result = model.invoke(prompt)
# print(result.content)

template_multiple = """You are a helpful assistant.
Human: Tell me a {adjective} story about a {animal}.
Assistant:"""
prompt_template_multiple = ChatPromptTemplate.from_template(template_multiple)

prompt_multiple = prompt_template_multiple.invoke({
  'adjective': 'sad', 
  'animal': 'zebra',
})
# result = model.invoke(prompt_multiple)
# print(result.content)

# print(prompt_multiple)

messages = [
  ('system', 'You are a comedian who tells jokes about {topic}'), 
  ('human', 'Tell me {joke_count} jokes.')
]

prompt_template = ChatPromptTemplate.from_messages(messages)
prompt = prompt_template.invoke({
  'topic': 'philosophers of mind', 
  'joke_count': 10,
})
result = model.invoke(prompt) 
print(result.content)
# print(prompt)