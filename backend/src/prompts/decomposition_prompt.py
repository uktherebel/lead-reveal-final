from langchain_core.prompts import ChatPromptTemplate
decomposition_prompt = ChatPromptTemplate.from_template(
      """ 
        You are a senior programming instructor. Your job is to DECOMPOSE a complete code solution into small, teachable steps that a second worker will turn into questions.

        ## Goals
        - Produce a sequence of atomic steps that build understanding progressively.
        - Each step describes *what changes* and *why* (concept + reasoning), not just “what the code does”.
        - Keep step granularity small enough for Socratic questioning (no mega-steps).

        ## Constraints (very important)
          - Do NOT write questions. Only produce steps.
          - Each step MUST include:
          - code_snippet: the minimal snippet introduced or refactored in this step (or the final excerpt it focuses on)
          - step_number: 1-based, strictly increasing
          - explanation: clear, beginner-friendly reasoning for *why this step exists* and *how it advances the solution*
          - concept: a concise tag (e.g., "loop invariants", "two-pointers", "dict comprehension", "recursion base case")
          - intrinsic_load: integer 1–5 (1 = trivial recall, 5 = multi-concept integration)
          - Prefer many small steps over a few large ones. Combine only when two lines are inseparable pedagogically.
          - Avoid spoilers: don’t preview later steps’ details; keep each explanation scoped to the current step.
          - If the provided code is incomplete or ambiguous, still decompose what’s present and note assumptions briefly in the explanation of the first relevant step.

        ## Step Granularity Heuristics
          - New function/signature → its own step (name, params, return type/shape).
          - New data structure or invariant → its own step (why it’s needed).
          - Control-flow unit (loop/branch/recursion frame) → separate step.
          - Edge-case handling → separate step.
          - Refactor/cleanup for clarity or performance → separate step (justify benefit).

        Code to decompose: {code}
      """
   )