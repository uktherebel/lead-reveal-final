import asyncio
import logging
import uuid
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field, BaseModel

from src.state.schemas import Question
from src.workers.base_worker import BaseWorker

logger = logging.getLogger(__name__)

# Semaphore for the single mega call
MEGA_SEM = asyncio.Semaphore(1)  # Only one mega batch at a time

class QuestionsByLevel(BaseModel):
    """Questions for a single step at a specific cognitive level"""
    cognitive_level: int = Field(..., description="The cognitive level (1-5)")
    questions: List[Question] = Field(default_factory=list, description="Questions at this level")

class StepWithAllQuestions(BaseModel):
    """All questions for a single step across all cognitive levels"""
    step_number: int = Field(..., description="The step number")
    questions_by_level: List[QuestionsByLevel] = Field(default_factory=list, description="Questions organized by cognitive level")

class MegaBatchQuestionsOut(BaseModel):
    """Complete output for ALL steps with ALL questions at ALL cognitive levels"""
    steps_with_questions: List[StepWithAllQuestions] = Field(default_factory=list, description="All steps with all their questions")

class MegaBatchQuestionWorker(BaseWorker):
    """Worker that generates ALL questions for ALL steps at ALL cognitive levels in ONE single call"""
    
    def _setup(self):
        self.model = self.llm.with_structured_output(MegaBatchQuestionsOut, method="function_calling")
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of abstract process method"""
        return await self.process_mega_batch(**input_data)
    
    def _format_steps_info(self, steps: List[Dict[str, Any]]) -> str:
        """Format steps info for the mega prompt"""
        steps_text = ""
        for step in steps:
            steps_text += f"""
Step {step['step_number']}:
- Code snippet: {step['code_snippet']}
- Concept: {step['concept']}
- Explanation: {step['explanation']}
- Intrinsic load: {step.get('intrinsic_load', 3)}

"""
        return steps_text.strip()
    
    async def process_mega_batch(self,
                                *,
                                steps: List[Dict[str, Any]],
                                code: str, 
                                n_per_level: int = 1) -> Dict[str, Any]:
        """Generate ALL questions for ALL steps at ALL cognitive levels in ONE single call"""
        
        try:
            steps_info = self._format_steps_info(steps)
            
            # Create the mega prompt
            mega_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are creating questions for a complete coding solution across MULTIPLE STEPS and ALL COGNITIVE LEVELS in a single response.

For each step provided, you must generate {n_per_level} questions at EACH of the 5 cognitive levels:

**Cognitive Level 1 - RECALL**: Basic identification, simple recognition, terminology, output prediction
**Cognitive Level 2 - APPLICATION**: How to modify, what happens if changed, apply patterns
**Cognitive Level 3 - ANALYSIS**: Why does this work, time complexity, find bugs, compare approaches  
**Cognitive Level 4 - EVALUATION**: Which is better and why, critique decisions, assess trade-offs
**Cognitive Level 5 - CREATION**: How to extend, design test cases, refactor, build upon this

You will receive the complete code solution and multiple steps. Generate questions systematically for ALL steps at ALL levels.

Return in the exact JSON structure specified."""),
                ("human", """
Complete Code Solution: {code}

Steps to generate questions for:
{steps_info}

Generate {n_per_level} questions for EACH step at EACH of the 5 cognitive levels.

Return as JSON with this structure:
{{
    "steps_with_questions": [
        {{
            "step_number": 1,
            "questions_by_level": [
                {{
                    "cognitive_level": 1,
                    "questions": [
                        {{
                            "question": "What does this line of code do?",
                            "options": ["A", "B", "C", "D"],
                            "correct_answer": 0,
                            "explanation": "Explanation here",
                            "cognitive_load": 1
                        }}
                    ]
                }},
                {{
                    "cognitive_level": 2,
                    "questions": [...]
                }},
                ... (continue for all 5 levels)
            ]
        }},
        ... (continue for all steps)
    ]
}}
""")
            ])
            
            formatted_prompt = mega_prompt.format_messages(
                code=code,
                steps_info=steps_info,
                n_per_level=n_per_level
            )
            
            # Use semaphore to control this mega call
            async with MEGA_SEM:
                print(f"MEGA BATCH: Starting single call for {len(steps)} steps across all 5 cognitive levels")
                response: MegaBatchQuestionsOut = await self.execute_with_retry(
                    lambda: self.model.ainvoke(formatted_prompt)
                )
                print(f"MEGA BATCH: Completed single mega call")
            
            # Convert to the expected format and assign IDs
            final_steps = []
            for step_with_questions in response.steps_with_questions:
                step_number = step_with_questions.step_number
                
                # Find the original step data
                original_step = None
                for s in steps:
                    if s.get("step_number") == step_number:
                        original_step = s
                        break
                
                if not original_step:
                    continue
                
                # Collect all questions from all cognitive levels
                all_questions = []
                for questions_by_level in step_with_questions.questions_by_level:
                    cognitive_level = questions_by_level.cognitive_level
                    for q in questions_by_level.questions:
                        question_dict = q.model_dump()
                        question_dict['id'] = str(uuid.uuid4())
                        question_dict['cognitive_load'] = cognitive_level
                        all_questions.append(question_dict)
                
                # Create final step with all questions
                final_step = {
                    **original_step,
                    "questions": all_questions
                }
                final_steps.append(final_step)
                
                print(f"MEGA BATCH: Step {step_number} - {len(all_questions)} total questions across all levels")
            
            total_questions = sum(len(step.get("questions", [])) for step in final_steps)
            print(f"MEGA BATCH: Generated {total_questions} total questions for {len(final_steps)} steps in ONE call")
            
            return {
                'success': True,
                'steps': final_steps,
                'total_questions': total_questions
            }
            
        except Exception as e:
            logger.error(f"Mega batch question generation failed: {e}")
            return await self.handle_error(e, {
                "num_steps": len(steps),
                "n_per_level": n_per_level
            })