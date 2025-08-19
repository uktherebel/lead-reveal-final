import asyncio
import sys
from pathlib import Path
import json
import time

# Add backend to path
current_file = Path(__file__).resolve()
backend_path = current_file.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Store original working directory
import os
original_cwd = os.getcwd()

import streamlit as st

# Import backend services with error handling
try:
    from src.graphs.subgraphs.build_assets_graph import build_assets_app
    from src.graphs.learn_nodes import choose_next_question
    from src.state.schemas import create_initial_state
    from services.hints import request_dynamic_hint
    BACKEND_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Backend import failed: {e}")
    BACKEND_AVAILABLE = False

st.set_page_config(
    page_title="Lead Reveal - Interactive Learning",
    page_icon="🎓",
    layout="wide"
)

def init_session_state():
    """Initialize Streamlit session state"""
    if 'learning_state' not in st.session_state:
        st.session_state.learning_state = None
    if 'current_step_questions' not in st.session_state:
        st.session_state.current_step_questions = []
    if 'stage' not in st.session_state:
        st.session_state.stage = 'input'  # input, generating, learning, completed
    if 'last_answer_result' not in st.session_state:
        st.session_state.last_answer_result = None
    if 'current_hint' not in st.session_state:
        st.session_state.current_hint = None

async def generate_content(task_description, difficulty):
    """Generate code and questions for the task"""
    state = {
        "task_description": task_description,
        "difficulty_level": difficulty,
        "code_solution": "",
        "validated_code": "",
        "steps": [],
        "step_updates": [],
    }
    
    try:
        result = await asyncio.wait_for(
            build_assets_app.ainvoke(state),
            timeout=300.0  # 5 minute timeout
        )
        return result
    except asyncio.TimeoutError:
        st.error("⚠️ Content generation timed out. This can happen with complex tasks.")
        return None
    except Exception as e:
        st.error(f"❌ Content generation failed: {e}")
        return None

def display_code_solution(code):
    """Display the generated code solution"""
    st.subheader("📝 Generated Solution")
    st.code(code, language='python')

def display_learning_progress():
    """Display learning progress and stats"""
    state = st.session_state.learning_state
    if not state:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Score", state.get('score', 0))
    with col2:
        st.metric("Accuracy", f"{state.get('accuracy_rate', 0):.1%}")
    with col3:
        st.metric("Questions Answered", len(state.get('user_answers', [])))
    with col4:
        st.metric("Hints Used", state.get('hints_used', 0))

def display_question():
    """Display current question and handle answers"""
    state = st.session_state.learning_state
    if not state or not state.get('current_question'):
        return False
    
    question = state['current_question']
    
    st.subheader("❓ Question")
    st.write(f"**Step {question.get('step_number', '?')}** (Difficulty Level {question.get('cognitive_load', '?')})")
    st.write(question['question'])
    
    # Display options if multiple choice
    if question.get('options'):
        options = question['options']
        answer = st.radio("Choose your answer:", options, key=f"q_{question.get('question_id', 'unknown')}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Submit Answer", type="primary"):
                return submit_answer(answer)
        with col2:
            if st.button("Get Hint"):
                return get_hint()
    else:
        # Text input for open-ended questions
        answer = st.text_area("Your answer:", key=f"q_{question.get('question_id', 'unknown')}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Submit Answer", type="primary", disabled=not answer.strip()):
                return submit_answer(answer.strip())
        with col2:
            if st.button("Get Hint"):
                return get_hint()
    
    return False

def submit_answer(user_answer):
    """Submit user answer and update state"""
    state = st.session_state.learning_state
    
    # Record response time (simplified)
    rt_seconds = 30.0  # In real app, track actual time
    
    try:
        # Use simplified version that doesn't require database
        from services.validators import ensure_current_question, validate_answer_shape
        from services.eval import is_correct, score_delta
        from services.bandit_lints import LinTS
        from services.adapt_context import context_x
        from services.adapt_reward import reward
        
        ensure_current_question(state)
        cq = state["current_question"]

        ans = validate_answer_shape(cq, user_answer)
        user_val = cq["options"][ans] if isinstance(ans, int) and cq.get("options") else ans

        correct = is_correct(user_val, cq["correct_answer"])
        
        # Update step questions
        i = state.get("current_step", 0)
        for q in state["steps"][i]["questions"]:
            if q.get("id") == cq["question_id"]:
                q["answered"] = True
                q["correct"] = correct
                break

        # Update scores
        delta = score_delta(correct)
        score = state.get("score", 0) + delta
        total = len(state.get("user_answers", [])) + 1
        corrects = sum(1 for a in state.get("user_answers", []) if a.get("correct")) + (1 if correct else 0)
        acc = corrects / total

        # Update bandit
        bandit = LinTS.from_dict(state["bandit"])
        r = reward(correct, state.get("hints_used", 0), False, rt_seconds)
        bandit.update(state["next_load_idx"], context_x(state), r)

        record = {
            "step_number": cq["step_number"],
            "question_id": cq["question_id"],
            "user_answer": user_val,
            "correct": correct,
            "rt": rt_seconds,
            "revealed": False,
        }

        # Update state
        state.update({
            "score": score,
            "accuracy_rate": acc,
            "user_answers": state.get("user_answers", []) + [record],
            "bandit": bandit.to_dict(),
        })
        
        # Show result
        if correct:
            st.success("✅ Correct! Well done.")
        else:
            st.error(f"❌ Incorrect. The correct answer was: {cq['correct_answer']}")
            if cq.get('explanation'):
                st.info(f"💡 Explanation: {cq['explanation']}")
        
        # Get next question
        next_q = choose_next_question(state)
        state.update(next_q)
        
        if state.get('completed'):
            st.session_state.stage = 'completed'
            st.balloons()
        
        st.rerun()
        return True
        
    except Exception as e:
        st.error(f"Error submitting answer: {e}")
        return False

def get_hint():
    """Get a hint for the current question"""
    state = st.session_state.learning_state
    
    try:
        # Use simplified hint (in real app, you'd use async request_dynamic_hint)
        current_q = state.get('current_question', {})
        hints_used = state.get('hints_used', 0)
        
        # Simple tier-based hint
        if hints_used == 0:
            hint = "💡 Think about the core concept being tested in this step."
        elif hints_used == 1:
            hint = "💡 Look at the specific code snippet and consider what each part does."
        else:
            hint = "💡 Check the variable names and control flow in the relevant section."
        
        state['hints_used'] = hints_used + 1
        
        st.info(hint)
        st.rerun()
        
    except Exception as e:
        st.error(f"Error getting hint: {e}")

def main():
    init_session_state()
    
    st.title("🎓 Lead Reveal - Interactive Programming Learning")
    st.markdown("Learn programming concepts through adaptive questioning and immediate feedback.")
    
    if st.session_state.stage == 'input':
        # Task input phase
        st.header("📋 Define Your Learning Task")
        
        task = st.text_area(
            "What programming concept or algorithm would you like to learn?",
            value="Write a BFS algorithm over adjacency list, return distance from source node.",
            height=100
        )
        
        if st.button("Start Learning", type="primary", disabled=not task.strip()):
            st.session_state.stage = 'generating'
            st.rerun()
    
    elif st.session_state.stage == 'generating':
        # Content generation phase
        st.header("⚡ Generating Your Learning Experience...")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Get task from previous input (in real app, store this properly)
        task = "Write a BFS algorithm over adjacency list, return distance from source node."
        difficulty = "intermediate"  # Default to intermediate
        
        status_text.text("Generating code solution...")
        progress_bar.progress(33)
        
        # Generate content
        result = asyncio.run(generate_content(task, difficulty))
        
        if result:
            progress_bar.progress(66)
            status_text.text("Creating questions...")
            
            # Initialize learning state
            learning_state = create_initial_state(task, "algorithms")
            learning_state.update({
                "validated_code": result.get("validated_code", ""),
                "steps": result.get("steps", []),
                "current_step": 0
            })
            
            # Start learning loop
            first_question = choose_next_question(learning_state)
            learning_state.update(first_question)
            
            st.session_state.learning_state = learning_state
            
            progress_bar.progress(100)
            status_text.text("Ready to start learning!")
            
            time.sleep(1)
            st.session_state.stage = 'learning'
            st.rerun()
        else:
            st.error("Failed to generate content. Please try again.")
            if st.button("Try Again"):
                st.session_state.stage = 'input'
                st.rerun()
    
    elif st.session_state.stage == 'learning':
        # Learning phase
        state = st.session_state.learning_state
        
        if state and state.get('validated_code'):
            display_code_solution(state['validated_code'])
        
        st.header("🎯 Interactive Learning")
        display_learning_progress()
        
        if not display_question():
            if state and state.get('completed'):
                st.session_state.stage = 'completed'
                st.rerun()
        
        # Sidebar with step info
        with st.sidebar:
            st.header("📊 Progress")
            if state:
                total_steps = len(state.get('steps', []))
                current_step = state.get('current_step', 0) + 1
                st.write(f"Step {min(current_step, total_steps)} of {total_steps}")
                
                # Show step details
                if current_step <= total_steps:
                    step = state['steps'][current_step - 1]
                    st.write(f"**Concept:** {step.get('concept', 'N/A')}")
                    st.write(f"**Code:** `{step.get('code_snippet', 'N/A')[:50]}...`")
    
    elif st.session_state.stage == 'completed':
        # Completion phase
        st.header("🎉 Learning Complete!")
        state = st.session_state.learning_state
        
        if state:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Final Score", state.get('score', 0))
            with col2:
                st.metric("Final Accuracy", f"{state.get('accuracy_rate', 0):.1%}")
            with col3:
                st.metric("Total Questions", len(state.get('user_answers', [])))
        
        if st.button("Start New Learning Session"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()