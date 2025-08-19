import streamlit as st
import asyncio
import sys
from pathlib import Path
import json
import time
import os

# Add backend to path without changing working directory
current_file = Path(__file__).resolve()
backend_path = current_file.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Try importing with error handling
try:
    # Test basic import first
    from src.state.schemas import create_initial_state
    st.success("✅ Backend connection successful!")
    
    # Now import the rest
    from src.graphs.subgraphs.build_assets_graph import build_assets_app
    from src.graphs.learn_nodes import choose_next_question
    
    BACKEND_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Backend import failed: {e}")
    st.error("Make sure you're running from the correct directory and backend is set up")
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
    if 'stage' not in st.session_state:
        st.session_state.stage = 'input'

def main():
    init_session_state()
    
    st.title("🎓 Lead Reveal - Interactive Programming Learning")
    st.markdown("Learn programming concepts through adaptive questioning and immediate feedback.")
    
    if not BACKEND_AVAILABLE:
        st.error("Backend services are not available. Please check your setup.")
        st.stop()
    
    if st.session_state.stage == 'input':
        st.header("📋 Define Your Learning Task")
        
        task = st.text_area(
            "What programming concept or algorithm would you like to learn?",
            value="Write a BFS algorithm over adjacency list, return distance from source node.",
            height=100
        )
        
        if st.button("Start Learning", type="primary", disabled=not task.strip()):
            # For now, just show a message
            st.success("Backend integration successful! Ready to generate content.")
            st.info("Content generation will be implemented once imports are working correctly.")
    
    # Debug info
    with st.expander("Debug Info"):
        st.write(f"Current working directory: {os.getcwd()}")
        st.write(f"Backend path: {backend_path}")
        st.write(f"Backend exists: {backend_path.exists()}")
        st.write(f"Python path: {sys.path[:3]}...")  # Show first 3 paths

if __name__ == "__main__":
    main()