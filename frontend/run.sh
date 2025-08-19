#!/bin/bash

# Make sure we're in the right directory
cd "$(dirname "$0")"

# Install requirements if needed
pip install -r requirements.txt

# Run the Streamlit app
streamlit run streamlit_app.py --server.port 8501 --server.headless false