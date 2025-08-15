from langchain_core.prompts import ChatPromptTemplate










question_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a master educator using the Socratic method.
            Create questions that:
            1. Guide learners to discover solutions themselves
            2. Test conceptual understanding, not memorization
            3. Build progressively in difficulty
            4. Include helpful hints that don't give away the answer
            5. Have one clearly correct answer among plausible distractors
            """),
            ("human", """
            Create a multiple-choice question for this code step:

            Step Number: {step_number}
            Code Snippet: {code_snippet}
            Explanation: {explanation}
            Concept: {concept}
            Cognitive Load: {cognitive_load}

            Requirements:
            - Question should test understanding of the concept
            - 4 answer options (A, B, C, D)
            - Include a helpful hint
            - Mark the correct answer

            Return as JSON:
            {{
                "question": "What does this code accomplish?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": 0,
                "hint": "Think about...",
                "explanation": "The correct answer is A because..."
            }}
            """)
        ])

cognitive_load_1_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are creating BASIC RECALL questions (Cognitive Load 1).
            Focus on:
            - Direct identification (What is this?)
            - Simple recognition (Which line does X?)
            - Basic terminology (What does this keyword mean?)
            - Output prediction (What prints?)
            
            Make it very straightforward - no tricks or deep analysis."""),
            ("human", """
            Code: {code}
             
            Step_number: {step_num}
            Relevant code snippet: {code_snippet}
            Explanation: {explanation}
            Concept: {concept}
            
            Create a simple recall question with 4 options.
            Return as JSON:
            {{
                "question": "What does this code output?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0,
                "hint": "Look at the print statement",
                "explanation": "Simple explanation"
            }}
            """)
        ])

