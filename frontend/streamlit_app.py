import os
import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import streamlit as st


def _add_path(p: Path) -> None:
    p = p.resolve()
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

def _auto_find_repo_root() -> Optional[Path]:
    here = Path(__file__).resolve()
    for cand in [here.parent, *here.parents]:
        if (cand / "backend").exists():
            return cand
    return None

def _try_import_build_graph() -> tuple[Optional[object], Optional[Exception]]:
    try_order = [
        "backend.src.graphs.subgraphs.build_assets_graph",
        "src.graphs.subgraphs.build_assets_graph",
    ]
    last_err = None
    for mod in try_order:
        try:
            m = __import__(mod, fromlist=["build_assets_app"])
            return getattr(m, "build_assets_app", None), None
        except Exception as e:
            last_err = e
    return None, last_err

# Session init
if "repo_root" not in st.session_state:
    st.session_state.repo_root = None
if "import_error" not in st.session_state:
    st.session_state.import_error = None

# Try auto-detect first
if st.session_state.repo_root is None:
    auto = _auto_find_repo_root()
    if auto:
        st.session_state.repo_root = str(auto)

# Ensure path added if we have a repo_root
if st.session_state.repo_root:
    _add_path(Path(st.session_state.repo_root))

build_assets_app, import_err = _try_import_build_graph()
st.session_state.import_error = import_err

# ============== Sidebar: Repo root override if needed ========================

st.sidebar.title("Lead-Reveal Tutor")
with st.sidebar.expander("Repository settings", expanded=bool(import_err)):
    st.caption("If import fails, point this app to your **repo root** (the folder that contains `backend/`).")
    repo_root_in = st.text_input("Repo root path", value=st.session_state.repo_root or "")
    colx1, colx2 = st.columns([1,1])
    if colx1.button("Use this path"):
        st.session_state.repo_root = repo_root_in.strip() or None
        if st.session_state.repo_root:
            _add_path(Path(st.session_state.repo_root))
        build_assets_app, import_err = _try_import_build_graph()
        st.session_state.import_error = import_err
        if import_err is None and build_assets_app is not None:
            st.sidebar.success("Import succeeded.")
        else:
            st.sidebar.error(f"Import still failing: {repr(import_err)}")

    if colx2.button("Auto-detect"):
        auto = _auto_find_repo_root()
        if auto:
            st.session_state.repo_root = str(auto)
            _add_path(auto)
            build_assets_app, import_err = _try_import_build_graph()
            st.session_state.import_error = import_err
            if import_err is None and build_assets_app is not None:
                st.sidebar.success(f"Auto-detected repo at: {auto}")
            else:
                st.sidebar.error(f"Import still failing: {repr(import_err)}")
        else:
            st.sidebar.warning("Could not auto-detect. Enter path manually.")

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
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
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
            for step_idx, step in enumerate(steps):
                for j, q in enumerate(step.get("questions", [])):
                    if q.get("id") == current_question.get("question_id"):
                        return {"step_idx": step_idx, "q_idx": j, "step": step, "q": q}
        
        return None
        
    except Exception as e:
        # Fallback to sequential if adaptive fails
        print(f"Adaptive selection failed, falling back to sequential: {e}")
        return first_unanswered_fallback(state)

def first_unanswered_fallback(state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fallback sequential question selection"""
    for i, step in enumerate(state.get("steps", [])):
        for j, q in enumerate(step.get("questions", [])):
            if not q.get("answered"):
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

# Quick mode option
quick_mode = st.sidebar.checkbox(
    "⚡ Quick mode", 
    value=False, 
    help="Generate questions by cognitive level (5 calls max) instead of by step (faster)"
)

if quick_mode:
    st.sidebar.caption("🚀 Quick mode: Groups steps by cognitive level for batch generation")
else:
    st.sidebar.caption("🐢 Normal mode: Generates questions per step individually")

if "state" not in st.session_state:
    st.session_state.state = {}
if "ui" not in st.session_state:
    st.session_state.ui = {"timer_start": None, "reveal": False, "current_selection": None, "show_feedback": False}
if "last_error" not in st.session_state:
    st.session_state.last_error = None

async def _build_assets_async(progress_bar, status_text):
    if build_assets_app is None or st.session_state.import_error is not None:
        raise RuntimeError(
            "Build graph import failed. Set 'Repo root path' above so that 'backend/' is importable.\n"
            f"Import error: {repr(st.session_state.import_error)}"
        )
    
    # Initialize state
    status_text.text("Initializing learning session...")
    progress_bar.progress(10)
    state_data = init_learning_state(task, difficulty=difficulty)
    state_data["quick_mode"] = quick_mode  # Add quick mode flag
    st.session_state.state = state_data
    
    # Generate assets
    status_text.text("Generating code solution...")
    progress_bar.progress(30)
    
    # Call the async build process
    mode_text = "quick mode (batch by level)" if quick_mode else "normal mode (per step)"
    status_text.text(f"Generating questions using {mode_text}...")
    progress_bar.progress(50)
    
    out = await build_assets_app.ainvoke(st.session_state.state)
    
    status_text.text("Processing steps and questions...")
    progress_bar.progress(80)
    
    # Update state
    st.session_state.state.update(out)
    st.session_state.ui["current_selection"] = None
    st.session_state.ui["timer_start"] = time.time()
    st.session_state.last_error = None
    
    # Complete
    status_text.text("Assets built successfully!")
    progress_bar.progress(100)

def _build_assets():
    # Create progress indicators
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        asyncio.run(_build_assets_async(progress_bar, status_text))
        time.sleep(0.5)  # Brief pause to show completion
        progress_bar.empty()
        status_text.empty()
        return True
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        raise e

def _reset_session():
    st.session_state.state = {}
    st.session_state.ui = {"timer_start": None, "reveal": False, "current_selection": None, "show_feedback": False}
    st.session_state.last_error = None

colA, colB = st.sidebar.columns([1,1])
if colA.button("🔨 Build assets", type="primary"):
    try:
        success = _build_assets()
        if success:
            st.sidebar.success("Assets built successfully!")
    except Exception as e:
        st.session_state.last_error = str(e)
        st.sidebar.error(f"Build failed: {e}")

if colB.button("♻️ Reset"):
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

st.title("Lead-Reveal Tutor — Build ▸ Learn")

if st.session_state.import_error is not None:
    st.warning(f"Build graph import is not ready: {repr(st.session_state.import_error)}. "
               "Set the 'Repo root path' in the sidebar so that 'backend/' is importable.")

if st.session_state.last_error:
    st.error(st.session_state.last_error)

state = st.session_state.state or {}
steps = state.get("steps", [])

left, right = st.columns([1.2, 1.8], gap="large")

with left:
    st.subheader("Generated code")
    code = state.get("validated_code") or state.get("code_solution") or ""
    if code:
        st.code(code, language="python")
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
    st.subheader("Practice (temporary local loop)")
    if not steps:
        st.info("Build assets first.")
    else:
        # Show progress
        total_questions = sum(len(s.get("questions", [])) for s in steps)
        answered_questions = sum(len([q for q in s.get("questions", []) if q.get("answered")]) for s in steps)
        
        # Debug: Show question count per step
        if st.sidebar.checkbox("🔍 Debug Questions"):
            st.sidebar.write("Question Debug Info:")
            for i, step in enumerate(steps):
                questions = step.get("questions", [])
                answered_in_step = sum(1 for q in questions if q.get("answered"))
                st.sidebar.write(f"Step {i+1}: {len(questions)} questions ({answered_in_step} answered)")
                # Show step details for debugging
                st.sidebar.caption(f"  Step number: {step.get('step_number')}")
                st.sidebar.caption(f"  Concept: {step.get('concept', 'No concept')}")
                st.sidebar.caption(f"  Code snippet length: {len(step.get('code_snippet', ''))}")
                st.sidebar.caption(f"  Intrinsic load: {step.get('intrinsic_load', 'NOT SET')}")
                if questions:
                    for j, q in enumerate(questions[:2]):  # Show first 2 questions
                        answered_status = "✓" if q.get("answered") else "○"
                        st.sidebar.caption(f"Q{j+1} {answered_status}: {q.get('question', 'No question')[:50]}...")
            st.sidebar.write(f"Total: {total_questions} questions")
            
            # Show full state for debugging
            if st.sidebar.checkbox("🐛 Show Full State"):
                st.sidebar.write("Full State:")
                st.sidebar.json({
                    "steps_count": len(steps),
                    "current_step": state.get("current_step", 0),
                    "total_questions": total_questions,
                    "answered_questions": answered_questions,
                    "session_id": state.get("session_id"),
                    "quick_mode": state.get("quick_mode"),
                    "has_bandit": bool(state.get("bandit"))
                })
        
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

                opts = q.get("options", [])
                if opts:
                    choice = st.radio(
                        "Choose one:",
                        options=list(range(len(opts))),
                        format_func=lambda k: f"{k}. {str(opts[k])}",
                        index=0,
                        key=f"radio_{q.get('id', f'{i}_{j}')}"
                    )
                else:
                    choice = st.text_input("Your answer (free text)", value="")

                c1, c2, c3, c4 = st.columns([1,1,1,1])

                # Hint (non-revealing for demo): show step explanation
                if c1.button("💡 Hint"):
                    st.session_state.state["hints_used"] = int(st.session_state.state.get("hints_used", 0)) + 1
                    st.info(step.get("explanation","Think about what this step enforces."))

                # Reveal (demo)
                if c2.button("👁 Reveal"):
                    st.session_state.ui["reveal"] = True

                # Submit
                submit_disabled = False
                attempts = q.get("attempts", 0)
                max_attempts = 2
                
                if attempts >= max_attempts:
                    submit_disabled = True
                    st.info(f"Question completed ({attempts}/{max_attempts} attempts)")
                
                if c3.button("Submit", disabled=submit_disabled):
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
                            import sys
                            sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
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
                    
                    # Auto-advance if max attempts reached
                    if attempts >= max_attempts and not correct:
                        st.session_state.ui["auto_advance"] = True

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
                    
                    # Auto-advance or show Next button
                    if st.session_state.ui.get("auto_advance", False) or show_next:
                        st.markdown("---")  # Visual separator
                        col_next = st.columns([2, 1, 2])[1]  # Center the button
                        
                        # Auto-advance after delay or manual button
                        if st.session_state.ui.get("auto_advance", False):
                            if col_next.button("Continue ➡️", type="primary", use_container_width=True):
                                # Move to next question
                                st.session_state.ui["current_selection"] = None
                                st.session_state.ui["timer_start"] = time.time()
                                st.session_state.ui["show_feedback"] = False
                                st.session_state.ui["auto_advance"] = False
                                st.rerun()
                        elif show_next:
                            if col_next.button("Next Question ➡️", type="primary", use_container_width=True):
                                # Move to next question using adaptive selection
                                st.session_state.ui["current_selection"] = None
                                st.session_state.ui["timer_start"] = time.time()
                                st.session_state.ui["show_feedback"] = False
                                st.rerun()
                else:
                    # Show empty 4th column when no feedback
                    c4.empty()

                if st.session_state.ui.get("reveal", False):
                    st.warning(f"Reveal (demo): **Answer:** {q.get('correct_answer')}")
                with st.expander("Explanation", expanded=False):
                    st.write(q.get("explanation","(no explanation)"))
                
                # Debug info (remove this later)
                if st.sidebar.checkbox("🐛 Debug Mode"):
                    st.sidebar.write("UI State:")
                    st.sidebar.json({
                        "show_feedback": st.session_state.ui.get("show_feedback", False),
                        "last_answer_correct": st.session_state.ui.get("last_answer_correct", "N/A"),
                        "current_question": f"Step {i+1}, Q {j+1}",
                        "question_answered": q.get("answered", False)
                    })
        else:
            st.info("No questions generated yet. Build assets first to generate questions.")
