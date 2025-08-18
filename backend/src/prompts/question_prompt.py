from langchain_core.prompts import ChatPromptTemplate

cognitive_load_1_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are creating {n} BASIC RECALL questions (Cognitive Load 1).
            Focus on:
            - Direct identification (What is this?)
            - Simple recognition (Which line does X?)
            - Basic terminology (What does this keyword mean?)
            - Output prediction (What prints?)
            
            Make it very straightforward - no tricks or deep analysis."""),
            ("human", """
            Code: {code}
             
            Step_number: {step_number}
            Relevant code snippet: {code_snippet}
            Explanation: {explanation}
            Concept: {concept}
            
            Create a simple recall question with 4 options.
            Return as JSON:
            {{
                "question": "What does this code output?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0,
                "explanation": "Simple explanation" 
                "cognitive_load": 1
            }}
            """)
        ])

cognitive_load_2_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are creating {n} APPLICATION questions (Cognitive Load 2).
            Focus on:
            - How would you modify this to do Y?
            - What happens if we change X?
            - Which method would you use for Z?
            - Apply this pattern to a similar problem
            
            Test ability to use concepts, not just remember them."""),
            ("human", """
            Code: {code}
             
            Step_number: {step_number}
            Relevant code snippet: {code_snippet}
            Explanation: {explanation}
            Concept: {concept}
            
            Create an application question that tests using this concept.
            Return as JSON:
            {{
                "question": "What does this code output?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "for m in range(len(fruits)):"
                "explanation": "Simple explanation" 
                "cognitive_load": 2
            }}
            """)
        ])

cognitive_load_3_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are creating {n} ANALYSIS questions (Cognitive Load 3).
            Focus on:
            - Why does this approach work?
            - What's the time complexity?
            - Find the bug in this logic
            - Compare this with alternative approaches
            - Explain the relationship between components
            
            Require deeper understanding of how and why things work."""),
            ("human", """
            Code: {code}
             
            Step_number: {step_number}
            Relevant code snippet: {code_snippet}
            Explanation: {explanation}
            Concept: {concept}
            
            Create an analysis question that requires understanding relationships and logic.
            """)
        ])

cognitive_load_4_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are creating {n} EVALUATION questions (Cognitive Load 4).
            Focus on:
            - Which approach is better and why?
            - Critique this design decision
            - Justify the trade-offs made
            - Assess the code quality
            - Evaluate error handling adequacy
            
            Require judgment, critical thinking, and justification."""),
            ("human", """
            Code: {code}
             
            Step_number: {step_number}
            Relevant code snippet: {code_snippet}
            Explanation: {explanation}
            Concept: {concept}
            
            Create an evaluation question that requires critical judgment.
            The question should make learners think about trade-offs and design decisions.
            Return as JSON.
            """)
        ])

cognitive_load_5_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are creating {n} CREATION questions (Cognitive Load 5).
            Focus on:
            - How would you extend this to handle X?
            - Design a test case that would break this
            - Refactor this for better maintainability
            - Create an API that uses this pattern
            - Build upon this to solve a harder problem
            
            Require synthesis and creative problem-solving."""),
            ("human", """
            Code: {code}
             
            Step_number: {step_number}
            Relevant code snippet: {code_snippet}
            Explanation: {explanation}
            Concept: {concept}
            
            Create a question that requires designing or building something new.
            Should test ability to synthesize and create, not just analyze.
            Return as JSON.
            """)
        ])