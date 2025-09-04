from langchain_core.prompts import ChatPromptTemplate

def get_batch_prompt_for_level(level: int) -> ChatPromptTemplate:
    """Get the appropriate batch prompt for a cognitive level"""
    
    if level == 1:
        return batch_cognitive_load_1_prompt
    elif level == 2:
        return batch_cognitive_load_2_prompt
    elif level == 3:
        return batch_cognitive_load_3_prompt
    elif level == 4:
        return batch_cognitive_load_4_prompt
    elif level == 5:
        return batch_cognitive_load_5_prompt
    else:
        raise ValueError(f"Invalid cognitive level: {level}")

batch_cognitive_load_1_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are creating BASIC RECALL questions (Cognitive Load 1) for MULTIPLE steps in a single response.
    Focus on:
    - Direct identification (What is this?)
    - Simple recognition (Which line does X?)
    - Basic terminology (What does this keyword mean?)
    - Output prediction (What prints?)
    
    Make it very straightforward - no tricks or deep analysis.
    
    You will receive multiple steps and must generate {n_per_step} questions for EACH step.
    Return questions in the exact order of steps provided."""),
    ("human", """
    Complete Code Solution: {code}
    
    Steps to generate questions for:
    {steps_info}
    
    Generate {n_per_step} BASIC RECALL questions for each step above.
    Each question should test simple recall and recognition for that specific step.
    
    Return as JSON with this structure:
    {{
        "questions_by_step": [
            {{
                "step_number": 1,
                "questions": [
                    {{
                        "question": "What does this code output?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0,
                        "explanation": "Simple explanation",
                        "cognitive_load": 1
                    }}
                ]
            }},
            ...
        ]
    }}
    """)
])

batch_cognitive_load_2_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are creating APPLICATION questions (Cognitive Load 2) for MULTIPLE steps in a single response.
    Focus on:
    - How would you modify this to do Y?
    - What happens if we change X?
    - Which method would you use for Z?
    - Apply this pattern to a similar problem
    
    Test ability to use concepts, not just remember them.
    
    You will receive multiple steps and must generate {n_per_step} questions for EACH step.
    Return questions in the exact order of steps provided."""),
    ("human", """
    Complete Code Solution: {code}
    
    Steps to generate questions for:
    {steps_info}
    
    Generate {n_per_step} APPLICATION questions for each step above.
    Each question should test the ability to apply and use the concepts from that specific step.
    
    Return as JSON with this structure:
    {{
        "questions_by_step": [
            {{
                "step_number": 1,
                "questions": [
                    {{
                        "question": "How would you modify this code to handle empty input?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0,
                        "explanation": "Application explanation",
                        "cognitive_load": 2
                    }}
                ]
            }},
            ...
        ]
    }}
    """)
])

batch_cognitive_load_3_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are creating ANALYSIS questions (Cognitive Load 3) for MULTIPLE steps in a single response.
    Focus on:
    - Why does this approach work?
    - What's the time complexity?
    - Find the bug in this logic
    - Compare this with alternative approaches
    - Explain the relationship between components
    
    Require deeper understanding of how and why things work.
    
    You will receive multiple steps and must generate {n_per_step} questions for EACH step.
    Return questions in the exact order of steps provided."""),
    ("human", """
    Complete Code Solution: {code}
    
    Steps to generate questions for:
    {steps_info}
    
    Generate {n_per_step} ANALYSIS questions for each step above.
    Each question should test deep understanding of relationships and logic for that specific step.
    
    Return as JSON with this structure:
    {{
        "questions_by_step": [
            {{
                "step_number": 1,
                "questions": [
                    {{
                        "question": "Why does this approach work better than alternatives?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0,
                        "explanation": "Analysis explanation",
                        "cognitive_load": 3
                    }}
                ]
            }},
            ...
        ]
    }}
    """)
])

batch_cognitive_load_4_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are creating EVALUATION questions (Cognitive Load 4) for MULTIPLE steps in a single response.
    Focus on:
    - Which approach is better and why?
    - Critique this design decision
    - Justify the trade-offs made
    - Assess the code quality
    - Evaluate error handling adequacy
    
    Require judgment, critical thinking, and justification.
    
    You will receive multiple steps and must generate {n_per_step} questions for EACH step.
    Return questions in the exact order of steps provided."""),
    ("human", """
    Complete Code Solution: {code}
    
    Steps to generate questions for:
    {steps_info}
    
    Generate {n_per_step} EVALUATION questions for each step above.
    Each question should require critical judgment and evaluation for that specific step.
    
    Return as JSON with this structure:
    {{
        "questions_by_step": [
            {{
                "step_number": 1,
                "questions": [
                    {{
                        "question": "Evaluate the trade-offs of this design decision",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0,
                        "explanation": "Evaluation explanation",
                        "cognitive_load": 4
                    }}
                ]
            }},
            ...
        ]
    }}
    """)
])

batch_cognitive_load_5_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are creating CREATION questions (Cognitive Load 5) for MULTIPLE steps in a single response.
    Focus on:
    - How would you extend this to handle X?
    - Design a test case that would break this
    - Refactor this for better maintainability
    - Create an API that uses this pattern
    - Build upon this to solve a harder problem
    
    Require synthesis and creative problem-solving.
    
    You will receive multiple steps and must generate {n_per_step} questions for EACH step.
    Return questions in the exact order of steps provided."""),
    ("human", """
    Complete Code Solution: {code}
    
    Steps to generate questions for:
    {steps_info}
    
    Generate {n_per_step} CREATION questions for each step above.
    Each question should test synthesis and creative problem-solving for that specific step.
    
    Return as JSON with this structure:
    {{
        "questions_by_step": [
            {{
                "step_number": 1,
                "questions": [
                    {{
                        "question": "How would you extend this to solve a more complex problem?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0,
                        "explanation": "Creation explanation",
                        "cognitive_load": 5
                    }}
                ]
            }},
            ...
        ]
    }}
    """)
])