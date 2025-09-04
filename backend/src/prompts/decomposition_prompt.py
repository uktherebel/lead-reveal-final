from langchain_core.prompts import ChatPromptTemplate
decomposition_prompt = ChatPromptTemplate.from_template(
      """ 
        You are a senior programming instructor. Your job is to DECOMPOSE a complete code solution into small, teachable steps that a second worker will turn into questions.

        ## Goals
        - Produce logical steps that build understanding progressively.
        - Each step should represent a complete logical concept or algorithm phase.
        - Each step describes *what changes* and *why* (concept + reasoning), not just "what the code does".

        ## Constraints (very important)
          - Do NOT write questions. Only produce steps.
          - Each step MUST include:
          - code_snippet: the minimal snippet introduced or refactored in this step (or the final excerpt it focuses on)
          - step_number: 1-based, strictly increasing
          - explanation: clear, beginner-friendly reasoning for *why this step exists* and *how it advances the solution*
          - concept: a concise tag (e.g., "loop invariants", "two-pointers", "dict comprehension", "recursion base case")
          - intrinsic_load: integer 1–5 (1 = trivial recall, 5 = multi-concept integration)
          - IMPORTANT: Aim for 6-8 total steps maximum. Group multiple related lines together.
          - IGNORE these trivial elements entirely:
            * Import statements (from collections import deque, etc.)
            * Function signatures/definitions (def function_name(...):)
            * Docstrings and comments
            * Example usage/test code at the bottom
            * Variable declarations that are just setup
          - FOCUS on these core algorithm elements:
            * Data structure initialization for the algorithm
            * Main algorithm loops and logic
            * Key decision points and conditionals
            * Result processing and return logic
          - Don't create separate steps for: individual variable assignments within the same logical unit, or single lines within loops.
          - Avoid spoilers: don't preview later steps' details; keep each explanation scoped to the current step.

        ## Step Granularity Heuristics (Focus on Algorithm Core)
          - Step 1: Algorithm setup (initialize data structures needed for the algorithm)
          - Step 2-N: Major algorithm phases (main loops, key decision logic, processing phases)
          - Final step: Result handling (return/output logic)
          - Skip: imports, function signatures, docstrings, example usage
          - Each step should include the specific code lines that implement that logical concept

        Code to decompose: {code}
      """
   )