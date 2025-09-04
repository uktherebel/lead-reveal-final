from langchain_core.prompts import ChatPromptTemplate

decomposition_refine_prompt = ChatPromptTemplate.from_template(
    """
    You are a senior programming instructor. Refine the following AST-derived step skeletons.

    Rules:
    - Do NOT change step boundaries or step_number.
    - For each step, write a clear, beginner-friendly explanation of why the step exists and how it advances the solution.
    - You may slightly improve the 'concept' label if wording is off, but keep it concise.
    - Keep 'intrinsic_load' unless it's obviously wrong; adjust only if necessary.

    Return the same list shape with fields: step_number, code_snippet, explanation, concept, intrinsic_load.

    Code:
    {code}

    Steps JSON:
    {steps_json}
    """
)

