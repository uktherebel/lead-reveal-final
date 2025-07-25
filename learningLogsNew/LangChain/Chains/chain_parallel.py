from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_core.runnables.base import RunnableLambda, RunnableSequence, RunnableParallel

load_dotenv()

model = ChatOllama(
  model='qwen2.5-coder:7b', 
  base_url="http://localhost:11434",
)

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an expert product reviewer."),
        ("human", "List the main features of the product {product_name}."),
    ]
)

# def analyse_pros(features): 
#   pros_template = ChatPromptTemplate.from_messages(
#     [
#       ('system', 'You are an expert product reviewer'), 
#       ('human', 'Given these features: {features}, list the '
#       'pros of these features')
#     ]
#   )
#   return pros_template.format_prompt(features=features) 


def analyse_pros(): 
  pros_template = ChatPromptTemplate.from_messages(
    [
      ('system', 'You are an expert product reviewer'), 
      ('human', 'Given these features: {features}, list the '
      'pros of these features')
    ]
  )
  return pros_template


# def analyse_cons(features): 
#   cons_prompt = ChatPromptTemplate.from_messages(
#     [
#       ('system', 'You\'re an expert product reviewer'), 
#       ('human', 'Given these features: {features}, give the cons of these features.')
#     ]
#   )
#   return cons_prompt.format_prompt(features=features)

def analyse_cons(): 
  cons_prompt = ChatPromptTemplate.from_messages(
    [
      ('system', 'You\'re an expert product reviewer'), 
      ('human', 'Given these features: {features}, give the cons of these features.')
    ]
  )
  return cons_prompt


def combine_pros_cons(pros, cons): 
  return f"Pros:\n{pros}\n\nCons:\n{cons}"

pros_branch_chain = (
  # RunnableLambda(lambda x: analyse_pros(x)) | 
  analyse_pros() |
  model | 
  StrOutputParser()
)

cons_branch_chain = (
  # RunnableLambda(lambda x : analyse_cons(x)) | 
  analyse_cons() |
  model | 
  StrOutputParser()
)

features_chain = prompt_template | model | StrOutputParser()

chain = (
  features_chain
  | RunnableParallel(branches = {'pros': pros_branch_chain, 'cons': cons_branch_chain})
  | RunnableLambda(lambda x : combine_pros_cons(x['branches']['pros'], x['branches']['cons']))
)

result = chain.invoke({
  'product_name': 'MacBook Pro M1'
})

print(result)