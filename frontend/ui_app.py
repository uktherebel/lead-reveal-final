import os
import sys
import json
import time
import asyncio
import random
from pathlib import Path
from typing import Optional, Dict, Any
# Ensure backend/src is importable as top-level 'src'
backend_root = Path(__file__).resolve().parent.parent / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
from src.graphs.subgraphs.build_assets_graph import build_assets_app
from src.graphs.subgraphs.batch_questions_subgraph import compiled_batch_graph
import streamlit as st


# =========================
# Minimal helpers
# =========================


def _new_session_id() -> str:
    import uuid, time as _t
    return f"session_{int(_t.time())}_{uuid.uuid4().hex[:6]}"

def init_learning_state(task: str, difficulty: str = "intermediate", technique: str = "lead-reveal") -> Dict[str, Any]:
    return {
        "session_id": _new_session_id(),
        "user_id": None,
        "task_description": task,
        "difficulty_level": difficulty,
        "technique": technique,
        "validated_code": "",
        "steps": [],
        "step_updates": [],
        "current_phase": "initialization",
        "current_step": 0,
        "total_steps": 0,
        "current_question": None,
        "user_answers": [],
        "score": 0,
        "accuracy_rate": 0.0,
        "hints_used": 0,
        "bandit": None,  # Will be initialised by choose_next_question
        "rolling_stats": {},  # For bandit context
        "next_load_idx": None,  # For bandit logic
    }

def get_next_question_adaptive(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Use LinTS bandit to adaptively select the next question based on cognitive load"""
    try:
        # Import the adaptive question selection logic
        from src.graphs.learn_nodes import choose_next_question
        
        # Use the bandit algorithm to choose the next question
        result = choose_next_question(state)
        
        if result.get("completed"):
            return None
            
        # Update state with bandit results
        if "bandit" in result:
            state["bandit"] = result["bandit"]
        if "next_load_idx" in result:
            state["next_load_idx"] = result["next_load_idx"]
        if "current_step" in result:
            state["current_step"] = result["current_step"]
            
        # Extract question details from the result
        current_question = result.get("current_question")
        if current_question:
            # Find the step and question indices across all steps
            steps = state.get("steps", [])
            if not steps:
                return None
            for step_idx, step in enumerate(steps):
                if not step:
                    continue
                for j, q in enumerate(step.get("questions", [])):
                    if q and q.get("id") == current_question.get("question_id"):
                        return {"step_idx": step_idx, "q_idx": j, "step": step, "q": q}
        
        return None
        
    except Exception as e:
        # Fallback to sequential if adaptive fails
        print(f"Adaptive selection failed, falling back to sequential: {e}")
        return first_unanswered_fallback(state)

def first_unanswered_fallback(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fallback sequential question selection"""
    steps = state.get("steps", [])
    if not steps:
        return None
    for i, step in enumerate(steps):
        if not step:
            continue
        questions = step.get("questions", [])
        if not questions:
            continue
        for j, q in enumerate(questions):
            if q and not q.get("answered"):
                return {"step_idx": i, "q_idx": j, "step": step, "q": q}
    return None

def normalize_answer(q: Dict[str, Any], choice) -> Dict[str, Any]:
    opts = q.get("options", [])
    if opts:
        idx = int(choice)
        return {"index": idx, "value": opts[idx]}
    else:
        return {"text": str(choice).strip()}

def is_correct(user, correct) -> bool:
    def _norm(x):
        return str(x).strip().lower().replace("’","'").replace("“",'"').replace("”",'"')
    if isinstance(user, dict):
        if "value" in user:
            return _norm(user["value"]) == _norm(correct)
        if "text" in user:
            return _norm(user["text"]) == _norm(correct)
    return _norm(user) == _norm(correct)

def update_metrics_after_submit(state: Dict[str, Any], record: Dict[str, Any]):
    if record.get("correct"):
        state["score"] = int(state.get("score", 0)) + 10
    ua = state.get("user_answers", [])
    corrects = sum(1 for r in ua if r.get("correct"))
    total = len(ua)
    state["accuracy_rate"] = (corrects / total) if total else 0.0

# =========================
# App layout
# =========================

st.set_page_config(page_title="Lead-Reveal Tutor (Demo)", layout="wide")

task_default = "Write a BFS over adjacency list; return distance (levels) from a source node."
task = st.sidebar.text_area("Task / instructions", value=task_default, height=110)
difficulty = st.sidebar.selectbox("Difficulty", ["beginner", "intermediate", "advanced"], index=1)

# Generation mode (mutually exclusive)
gen_mode = st.sidebar.radio(
    "Generation mode",
    ["Normal", "Quick", "Super quick"],
    index=0,
    help="Choose how questions are generated"
)
quick_mode = gen_mode == "Quick"
super_quick_mode = gen_mode == "Super quick"

# Place quick-mode explanation immediately under the checkbox
if super_quick_mode:
    st.sidebar.caption("🚀 Super quick: All steps, all levels, single batch (⚠️ **DISABLED**)")
    st.sidebar.warning("Super Quick mode is currently disabled - will use Normal mode")
elif quick_mode:
    st.sidebar.caption("⚡ Quick mode: Groups steps by cognitive level for batch generation (⚠️ **DISABLED**)")
    st.sidebar.warning("Quick mode is currently disabled - will use Normal mode")
else:
    st.sidebar.caption("🐢 Normal mode: Generates questions per step individually")

# Decomposition strategy toggle
decomp_choice = st.sidebar.selectbox(
    "Decomposition strategy",
    ["AST + LLM (recommended)", "LLM only"],
    index=0,
)
decomp_strategy = "ast_llm" if decomp_choice.startswith("AST") else "llm_only"

# Code validation toggle
enable_validation = st.sidebar.checkbox(
    "Enable code validation",
    value=True,
    help="Validate generated code in secure sandbox before showing results. May add 5-10s latency but ensures code safety and correctness."
)

if enable_validation:
    st.sidebar.caption("🛡️ Code will be validated for safety, syntax, and tested before display")
else:
    st.sidebar.caption("⚠️ Code will be shown immediately without validation (faster but potentially unsafe)")

# Show detected language from backend (will be populated after processing)
if "state" in st.session_state and st.session_state.state.get("programming_language"):
    detected_lang = st.session_state.state.get("programming_language", "python")
    st.sidebar.info(f"🔍 **Detected Language:** {detected_lang.title()}")
    if detected_lang != 'python':
        st.sidebar.warning("⚠️ Validation only works with Python code. Other languages will skip validation.")
else:
    st.sidebar.info("🔍 **Language:** Will be detected from task description")

# Use unified build graph (handles quick/normal internally)
build_assets_graph = build_assets_app

if "state" not in st.session_state:
    st.session_state.state = {}
if "ui" not in st.session_state:
    st.session_state.ui = {"timer_start": None, "reveal": False, "current_selection": None, "show_feedback": False}
if "last_error" not in st.session_state:
    st.session_state.last_error = None

QUOTES = [
    "Programs must be written for people to read, and only incidentally for machines to execute. — Harold Abelson",
    "Talk is cheap. Show me the code. — Linus Torvalds",
    "The only way to learn a new programming language is by writing programs in it. — Dennis Ritchie",
    "First, solve the problem. Then, write the code. — John Johnson",
    "Never trust a computer you can’t throw out a window. — Steve Wozniak",
]


async def _build_assets_async(progress_bar, status_text, quote_box):    
    # Initialise state
    status_text.text("Initializing learning session...")
    progress_bar.progress(10)
    quote_box.info(random.choice(QUOTES))
    state_data = init_learning_state(task, difficulty=difficulty)
    state_data["quick_mode"] = quick_mode  # Add quick mode flag
    state_data["super_quick_mode"] = super_quick_mode
    state_data["decomp_strategy"] = decomp_strategy
    state_data["enable_validation"] = enable_validation  # Add validation flag
    st.session_state.state = state_data
    
    # Apply decompose strategy for worker
    os.environ["DECOMP_STRATEGY"] = decomp_strategy

    # Generate assets
    status_text.text("Generating code solution...")
    progress_bar.progress(30)
    quote_box.info(random.choice(QUOTES))
    
    # Call the async build process
    if super_quick_mode:
        mode_text = "super quick mode (DISABLED - using normal mode)"
    elif quick_mode:
        mode_text = "quick mode (DISABLED - using normal mode)"
    else:
        mode_text = "normal mode (per step)"
    status_text.text(f"Using {decomp_strategy} | Generating questions via {mode_text}...")
    progress_bar.progress(50)
    quote_box.info(random.choice(QUOTES))
    
    out = await build_assets_graph.ainvoke(st.session_state.state)
    
    status_text.text("Processing steps and questions...")
    progress_bar.progress(80)
    quote_box.info(random.choice(QUOTES))
    
    # Update state
    st.session_state.state.update(out)
    st.session_state.ui["current_selection"] = None
    st.session_state.ui["timer_start"] = time.time()
    st.session_state.last_error = None
    
    # Complete
    status_text.text("Assets built successfully!")
    progress_bar.progress(100)
    quote_box.empty()

def _build_assets():
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    quote_box = st.empty()
    
    try:
        asyncio.run(_build_assets_async(progress_bar, status_text, quote_box))
        time.sleep(0.5)  # Brief pause to show completion
        progress_bar.empty()
        status_text.empty()
        quote_box.empty()
        return True
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        raise e

def _reset_session():
    st.session_state.state = {}
    st.session_state.first_run = True
    st.session_state.ui = {"timer_start": None, "reveal": False, "current_selection": None, "show_feedback": False}
    st.session_state.last_error = None

colA, colB = st.sidebar.columns([1,1])
if colA.button("Build assets", type="primary"):
    try:
        success = _build_assets()
        if success:
            st.sidebar.success("Assets built successfully!")
    except Exception as e:
        st.session_state.last_error = str(e)
        st.sidebar.error(f"Build failed: {e}")

if colB.button("Reset"):
    _reset_session()
    st.sidebar.info("Session reset.")

with st.sidebar.expander("Save / Load snapshot"):
    if st.button("💾 Download state JSON"):
        if st.session_state.state:
            content = json.dumps(st.session_state.state, indent=2, ensure_ascii=False)
            st.download_button("Download", data=content, file_name=f"{st.session_state.state.get('session_id','state')}.json", mime="application/json")
        else:
            st.warning("No state yet.")
    uploaded = st.file_uploader("Load state JSON", type=["json"])
    if uploaded is not None:
        try:
            st.session_state.state = json.loads(uploaded.read().decode("utf-8"))
            st.session_state.ui["current_selection"] = None
            st.session_state.ui["timer_start"] = time.time()
            st.sidebar.success("State loaded.")
        except Exception as e:
            st.sidebar.error(f"Load failed: {e}")

st.title("Lead-Reveal Tutor")

if st.session_state.last_error:
    st.error(st.session_state.last_error)

state = st.session_state.state or {}
steps = state.get("steps", [])

left, right = st.columns([1.2, 1.8], gap="large")

def _get_progress(track=True): 
        # Add null checks to prevent NoneType iteration errors
        safe_steps = steps if steps is not None else []
        total_questions = sum(len(s.get("questions", []) if s else []) for s in safe_steps if s is not None)
        answered_questions = sum(len([q for q in s.get("questions", []) if q and q.get("answered")]) for s in safe_steps if s is not None)
        if not track: 
            return total_questions == answered_questions
        return total_questions, answered_questions

with left:
    st.subheader("Generated code")
    code = state.get("validated_code") or state.get("code_solution") or ""
    
    # Display validation status if available
    validation_results = state.get("validation_results")
    
    if validation_results:
        if validation_results.get("valid"):
            if validation_results.get("test_results"):
                test_count = len(validation_results["test_results"])
                passed_count = sum(1 for t in validation_results["test_results"] if t.get("passed"))
                st.success(f"✅ Code validated: {passed_count}/{test_count} tests passed")
            else:
                st.success("✅ Code validated: Syntax and safety checks passed")
        else:
            error_msg = validation_results.get("error", "Validation failed")
            st.error(f"❌ Code validation failed: {error_msg}")
    elif enable_validation and code:
        st.warning("⚠️ Validation was enabled but no validation results found")
    elif not enable_validation and code:
        st.info("⚡ Validation disabled - code shown without safety checks")
    
    if code:
        with st.expander("Code reference", expanded=False):
            show_code = st.button('Show code')
            if _get_progress(track=False) or show_code: 
                st.code(code, language="python")
                
                # Show detailed validation info in expander if available
                if validation_results and show_code:
                    with st.expander("🛡️ Validation Details", expanded=False):
                        if validation_results.get("safety_check"):
                            safety = validation_results["safety_check"]
                            if safety.get("safe"):
                                st.success("🔒 Safety check: Passed")
                            else:
                                st.error(f"🚨 Safety issues: {', '.join(safety.get('issues', []))}")
                        
                        if validation_results.get("syntax_check"):
                            syntax = validation_results["syntax_check"]
                            if syntax.get("valid"):
                                st.success("📝 Syntax check: Valid Python code")
                            else:
                                st.error(f"📝 Syntax errors: {syntax.get('error', 'Unknown')}")
                        
                        if validation_results.get("test_results"):
                            st.write("🧪 **Test Results:**")
                            for test in validation_results["test_results"]:
                                status = "✅" if test.get("passed") else "❌"
                                test_name = test.get("assertion", f"Test {test.get('test_number', 'N/A')}")
                                st.write(f"{status} {test_name}")
            else: 
                st.code('')
    else:
        st.info("Build assets to see code.")

    st.subheader("Steps")
    if not steps:
        st.caption("No steps yet.")
    else:
        for i, step in enumerate(steps):
            with st.expander(f"Step {step.get('step_number', i+1)} — {step.get('concept','(no concept)')}", expanded=(i==0)):
                st.markdown(f"**Explanation**\n\n{step.get('explanation','(no explanation)')}")
                st.code(step.get("code_snippet",""), language="python")
                st.caption(f"{len(step.get('questions', []))} questions generated")

with right:
    st.subheader("Practice")
    if not steps:
        st.info("Build assets first.")
    else:
        # Show progress
        total_questions, answered_questions = _get_progress()
        
        # # Debug: Show question count per step
        # if st.sidebar.checkbox("Debug Questions"):
        #     st.sidebar.write("Question Debug Info:")
        #     for i, step in enumerate(steps):
        #         questions = step.get("questions", [])
        #         answered_in_step = sum(1 for q in questions if q.get("answered"))
        #         st.sidebar.write(f"Step {i+1}: {len(questions)} questions ({answered_in_step} answered)")
        #         # Show step details for debugging
        #         st.sidebar.caption(f"  Step number: {step.get('step_number')}")
        #         st.sidebar.caption(f"  Concept: {step.get('concept', 'No concept')}")
        #         st.sidebar.caption(f"  Code snippet length: {len(step.get('code_snippet', ''))}")
        #         st.sidebar.caption(f"  Intrinsic load: {step.get('intrinsic_load', 'NOT SET')}")
        #         if questions:
        #             for j, q in enumerate(questions[:2]):  # Show first 2 questions
        #                 answered_status = "✓" if q.get("answered") else "○"
        #                 st.sidebar.caption(f"Q{j+1} {answered_status}: {q.get('question', 'No question')[:50]}...")
        #     st.sidebar.write(f"Total: {total_questions} questions")
            
        #     # Show full state for debugging
        #     if st.sidebar.checkbox("Show Full State"):
        #         st.sidebar.write("Full State:")
        #         st.sidebar.json({
        #             "steps_count": len(steps),
        #             "current_step": state.get("current_step", 0),
        #             "total_questions": total_questions,
        #             "answered_questions": answered_questions,
        #             "session_id": state.get("session_id"),
        #             "quick_mode": state.get("quick_mode"),
        #             "has_bandit": bool(state.get("bandit"))
        #         })
        
        if total_questions > 0:
            progress = answered_questions / total_questions
            st.progress(progress, text=f"Progress: {answered_questions}/{total_questions} questions answered ({progress:.0%})")
            
            sel = st.session_state.ui.get("current_selection")
            if not sel:
                sel = get_next_question_adaptive(state)
                # Fallback to sequential if adaptive returns None but questions exist
                if not sel and total_questions > answered_questions:
                    sel = first_unanswered_fallback(state)
                st.session_state.ui["current_selection"] = sel
                st.session_state.ui["timer_start"] = time.time()

            if not sel:
                st.success("All questions answered 🎉")
            else:
                i, j = sel["step_idx"], sel["q_idx"]
                step, q = sel["step"], sel["q"]
                st.markdown(f"**Step {step.get('step_number', i+1)}** — *{step.get('concept','') or '(no concept)'}*")
                st.write(q.get("question","(no question)"))

                # Determine freeze/disable conditions for inputs
                attempts_now = int(q.get("attempts", 0))
                answered_flag = bool(q.get("answered", False))
                revealed_flag = bool(st.session_state.ui.get("reveal", False))
                max_attempts_local = 2
                freeze_inputs = revealed_flag or answered_flag or (attempts_now >= max_attempts_local)

                opts = q.get("options", [])
                if opts:
                    choice = st.radio(
                        "Choose one:",
                        options=list(range(len(opts))),
                        format_func=lambda k: f"{k}. {str(opts[k])}",
                        index=0,
                        key=f"radio_{q.get('id', f'{i}_{j}')}",
                        disabled=freeze_inputs
                    )
                else:
                    choice = st.text_input("Your answer (free text)", value="", disabled=freeze_inputs)

                c1, c2, c3, c4 = st.columns([1,1,1,1], gap="medium")

                # Hint (non-revealing for demo): show step explanation
                if c1.button("💡 Hint", disabled=freeze_inputs, use_container_width=True, help="hint-btn", type='secondary'):
                    st.session_state.state["hints_used"] = int(st.session_state.state.get("hints_used", 0)) + 1
                    st.info(step.get("explanation","Think about what this step enforces."))

                # Reveal (demo)
                reveal_disabled = answered_flag or (attempts_now >= max_attempts_local)
                if c2.button("👁 Reveal", disabled=reveal_disabled, use_container_width=True, help="reveal-btn", type='tertiary'):
                    st.session_state.ui["reveal"] = True
                    # Immediately rerun to apply disabled states to inputs
                    st.rerun()

                # Submit
                submit_disabled = False
                attempts = q.get("attempts", 0)
                max_attempts = 2
                
                if attempts >= max_attempts:
                    submit_disabled = True
                    st.info(f"Question completed ({attempts}/{max_attempts} attempts)")

                # Disable submit if revealed, attempts exhausted, or already answered correctly
                if st.session_state.ui["reveal"] or answered_flag:
                    submit_disabled = True
                
                if c3.button("Submit", disabled=submit_disabled, use_container_width=True, help="submit-btn", type='primary'):
                    start = st.session_state.ui.get("timer_start") or time.time()
                    rt = max(0.0, time.time() - start)

                    try:
                        # Use simplified adaptive learning logic to avoid async issues
                        user_norm = normalize_answer(q, choice)
                        user_val = user_norm.get("value", user_norm.get("text"))
                        correct = is_correct(user_val, q.get("correct_answer"))
                        revealed = bool(st.session_state.ui.get("reveal", False))

                        # Increment attempts
                        attempts += 1
                        state["steps"][i]["questions"][j]["attempts"] = attempts
                        
                        # Mark answered only if correct or max attempts reached
                        if correct or attempts >= max_attempts:
                            state["steps"][i]["questions"][j]["answered"] = True
                        
                        state["steps"][i]["questions"][j]["correct"] = bool(correct)

                        # Log user answer
                        record = {
                            "step_number": step.get("step_number", i+1),
                            "question_id": q.get("id"),
                            "user_answer": user_norm,
                            "correct": bool(correct),
                            "rt": round(rt, 3),
                            "revealed": revealed,
                            "attempt": attempts,
                        }
                        state.setdefault("user_answers", []).append(record)
                        update_metrics_after_submit(state, record)
                        
                        # Update bandit with reward from this answer
                        if state.get("bandit") and state.get("next_load_idx") is not None:
                            from services.bandit_lints import LinTS
                            from services.adapt_context import context_x
                            from services.adapt_reward import reward
                            
                            # Get the bandit and update it with the reward
                            bandit = LinTS.from_dict(state["bandit"])
                            context = context_x(state)
                            hints_used = state.get("hints_used", 0)
                            reward_value = reward(correct, hints_used, revealed, rt)
                            
                            # Update the bandit with the reward for the arm that was chosen
                            bandit.update(state["next_load_idx"], context, reward_value)
                            state["bandit"] = bandit.to_dict()
                            
                        elif not state.get("bandit"):
                            from services.bandit_lints import LinTS
                            state["bandit"] = LinTS(n_arms=5, d=6).to_dict()
                        
                    except Exception as e:
                        # Fallback to original logic
                        print(f"Adaptive submit failed, using fallback: {e}")
                        user_norm = normalize_answer(q, choice)
                        user_val = user_norm.get("value", user_norm.get("text"))
                        correct = is_correct(user_val, q.get("correct_answer"))

                        # Mark answered
                        state["steps"][i]["questions"][j]["answered"] = True
                        state["steps"][i]["questions"][j]["correct"] = bool(correct)

                        # Log user answer
                        record = {
                            "step_number": step.get("step_number", i+1),
                            "question_id": q.get("id"),
                            "user_answer": user_norm,
                            "correct": bool(correct),
                            "rt": round(rt, 3),
                            "revealed": bool(st.session_state.ui.get("reveal", False)),
                        }
                        state.setdefault("user_answers", []).append(record)
                        update_metrics_after_submit(state, record)

                    # Store feedback for display
                    st.session_state.ui["last_answer_correct"] = correct
                    st.session_state.ui["last_answer_time"] = rt
                    st.session_state.ui["last_attempt"] = attempts
                    st.session_state.ui["show_feedback"] = True

                    # Reset reveal state  
                    st.session_state.ui["reveal"] = False

                    # Rerun to immediately reflect any disabling (e.g., after correct or max attempts)
                    st.rerun()
                    
                    # Auto-advance if max attempts reached
                    # if attempts >= max_attempts and not correct:
                    #     st.session_state.ui["auto_advance"] = True

                # Show feedback if answer was just submitted
                if st.session_state.ui.get("show_feedback", False):
                    correct = st.session_state.ui.get("last_answer_correct", False)
                    rt = st.session_state.ui.get("last_answer_time", 0)
                    attempt_num = st.session_state.ui.get("last_attempt", 1)
                    
                    if correct:
                        st.success(f"🎉 Correct! Time: {rt:.1f}s | Score: {state.get('score', 0)}")
                        show_next = True
                    else:
                        if attempt_num == 1:
                            # First wrong attempt - don't show answer
                            st.error(f"❌ Incorrect. Try again! Time: {rt:.1f}s")
                            show_next = False
                        else:
                            # Second wrong attempt - show answer and advance
                            st.error(f"❌ Incorrect. Correct answer: **{q.get('correct_answer')}** | Time: {rt:.1f}s")
                            show_next = True
                    
                    # Auto-advance or show Next button (suppress if reveal is active to avoid duplicates)
                    if (st.session_state.ui.get("auto_advance", False) or show_next) and not st.session_state.ui.get("reveal", False):
                        st.markdown("---")  # Visual separator
                        col_next = st.columns([2, 1, 2])[1]  # Center the button
                        
                        # Auto-advance after delay or manual button
                        if st.session_state.ui.get("auto_advance", False):
                            if col_next.button("Continue ➡️", type="primary", use_container_width=True, help="next-btn"):
                                # Move to next question
                                st.session_state.ui["current_selection"] = None
                                st.session_state.ui["timer_start"] = time.time()
                                st.session_state.ui["show_feedback"] = False
                                st.session_state.ui["auto_advance"] = False
                                st.rerun()
                        elif show_next:
                            if col_next.button("Next Question", type="primary", use_container_width=True, help="next-btn"):
                                # Move to next question using adaptive selection
                                st.session_state.ui["current_selection"] = None
                                st.session_state.ui["timer_start"] = time.time()
                                st.session_state.ui["show_feedback"] = False
                                st.rerun()
                else:
                    # Show empty 4th column when no feedback
                    c4.empty()

                if st.session_state.ui.get("reveal", False):
                    st.warning(f"**Answer:** {q.get('correct_answer')}")

                    # After reveal, always show a single Next button (feedback area suppressed above)
                    st.markdown("---")
                    col_next_reveal = st.columns([2, 1, 2])[1]
                    if col_next_reveal.button(
                        "Next Question",
                        type="primary",
                        use_container_width=True,
                        help="next-btn",
                        key=f"next_reveal_{q.get('id', f'{i}_{j}')}"):
                        # Mark as answered to avoid resurfacing the same question
                        state["steps"][i]["questions"][j]["answered"] = True
                        # Reset UI state and advance
                        st.session_state.ui["current_selection"] = None
                        st.session_state.ui["timer_start"] = time.time()
                        st.session_state.ui["show_feedback"] = False
                        st.session_state.ui["reveal"] = False
                        st.rerun()

                # Show explanation when revealed, attempts exhausted, or answer is correct
                if (
                    st.session_state.ui.get("reveal", False)
                    or attempts >= max_attempts
                    or bool(q.get("correct", False))
                ):
                    with st.expander("Explanation", expanded=False):
                        st.write(q.get("explanation","(no explanation)"))
                
        else:
            st.info("No questions generated yet. Build assets first to generate questions.")
