# Lead Reveal - Streamlit Frontend

Interactive web interface for the Lead Reveal adaptive learning system.

## Features

- **Task Input**: Define programming learning tasks
- **Code Generation**: Automatically generate solutions
- **Interactive Questions**: Answer questions with adaptive difficulty
- **Real-time Feedback**: Get immediate results and hints
- **Progress Tracking**: Monitor learning progress and statistics
- **Adaptive Learning**: Questions adapt based on performance

## Quick Start

### Option 1: Using the run script
```bash
cd frontend
./run.sh
```

### Option 2: Manual setup
```bash
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open your browser to `http://localhost:8501`

## Prerequisites

1. **Backend setup**: Ensure the backend services are configured
2. **Database**: PostgreSQL should be running (Docker container works)
3. **Dependencies**: Python packages from backend should be available

## Usage Flow

1. **Define Task**: Enter a programming concept or algorithm to learn
2. **Wait for Generation**: System generates code solution and questions
3. **Learn Interactively**: Answer questions, get hints, track progress
4. **Complete**: View final scores and start new session

## Architecture

The Streamlit app integrates directly with:
- `build_assets_graph`: Generates code and questions
- `learn_nodes`: Manages question flow and evaluation  
- `services/*`: Handles validation, hints, and adaptive logic
- Backend state management for persistence

## Configuration

The app automatically:
- Adds backend path to Python imports
- Uses simplified evaluation (no database required)
- Handles async operations through `asyncio.run()`
- Manages session state through Streamlit

## Deployment

For production deployment:
1. Set up proper environment variables
2. Configure database connections  
3. Use production-ready ASGI server
4. Set up proper error handling and logging