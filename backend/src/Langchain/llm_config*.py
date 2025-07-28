from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain_ollama import ChatOllama
from langchain_core.runnables.base import RunnableLambda, RunnableParallel

load_dotenv()
model = ChatOllama(
  model='qwen2.5-coder:7b',
  base_url="http://localhost:11434",
)

system_message = ('system', 'You\'re an expert computer scientist.')
prompt_template = ChatPromptTemplate.from_messages(
  [
    system_message,
    ('human', 'Give step-by-step code and code explanations for this programming problem: {task}')
  ]
)

decomposition_template = ChatPromptTemplate.from_messages(
  [
    system_message, 
    ('human', 'Break the following solution into learnable steps:\n\n{code}')
  ]
)

decomposition_chain = RunnableLambda(
  lambda x : {'code': x} | 
  decomposition_template |
  model | 
  StrOutputParser()
  )

question_template = ChatPromptTemplate.from_messages(
  [
    system_message, 
    ('human', 'Create a Socratic question for each of the following steps:\n\n{steps}')
  ]
)

question_chain = RunnableLambda(
  lambda x : {'steps': x} | 
  question_template | 
  model | 
  StrOutputParser()
)

code_chain = prompt_template | model | StrOutputParser()

chain = (
  code_chain 
  | decomposition_chain 
  | question_chain
)

question = """
23. Merge k Sorted Lists
Hard
Topics
premium lock icon
Companies
You are given an array of k linked-lists lists, each linked-list is sorted in ascending order.

Merge all the linked-lists into one sorted linked-list and return it.


Example 1:

Input: lists = [[1,4,5],[1,3,4],[2,6]]
Output: [1,1,2,3,4,4,5,6]
Explanation: The linked-lists are:
[
  1->4->5,
  1->3->4,
  2->6
]
merging them into one sorted linked list:
1->1->2->3->4->4->5->6
Example 2:

Input: lists = []
Output: []
Example 3:

Input: lists = [[]]
Output: []
 

Constraints:

k == lists.length
0 <= k <= 104
0 <= lists[i].length <= 500
-104 <= lists[i][j] <= 104
lists[i] is sorted in ascending order.
The sum of lists[i].length will not exceed 104.
"""

result = chain.invoke(
  {'task': question}
)

print(result)