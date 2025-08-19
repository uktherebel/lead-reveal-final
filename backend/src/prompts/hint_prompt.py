from langchain_core.prompts import ChatPromptTemplate
_HINT_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You generate graded, attempt-aware hints for code questions.\n"
     "Constraints:\n"
     "1) Hint tier 1: conceptual nudge (no code).\n"
     "2) Tier 2: targeted scaffold referencing the step/concept (tiny pseudo if needed).\n"
     "3) Tier 3: point to the exact line/variable/pattern to check in the snippet.\n"
     "4) Never reveal the final answer.\n"),
    ("user",
     "Context:\n"
     "- Code snippet:\n{code_snippet}\n"
     "- Step concept: {concept}\n"
     "- Step explanation: {explanation}\n"
     "- Question: {question}\n"
     "- Options (maybe empty): {options}\n"
     "- User last answer (if any): {last_answer}\n"
     "- Hints used so far: {hints_used}\n"
     "- Response time z-score (rt_z): {rt_z}\n"
     "Generate a SINGLE hint for tier {tier}. Keep it 1-3 sentences. No solution reveal.")
])