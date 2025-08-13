from langchain_core.prompts import ChatPromptTemplate
decomposition_prompt = ChatPromptTemplate.from_template(
      """ 
        For the following code / programming problem: 
          - Decompose the code into meaningful, atomic steps that promote critical thinking and active learning.
        Code: {code}

        For each step, store the information in this format: 
        {format_instructions}
      """
   )