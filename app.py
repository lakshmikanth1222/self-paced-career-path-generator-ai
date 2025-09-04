# app.py

import streamlit as st
from utils import run_agent_sync
import os

st.set_page_config(page_title="MCP POC", page_icon="🤖", layout="wide")

st.title("Model Context Protocol(MCP) - Learning Path Generator")

# Initialize session state for progress
if 'current_step' not in st.session_state:
    st.session_state.current_step = ""
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'last_section' not in st.session_state:
    st.session_state.last_section = ""
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False

# Sidebar for optional configuration
st.sidebar.header("Optional Configuration")
st.sidebar.subheader("Pipedream URL")
notion_pipedream_url = st.sidebar.text_input("Notion URL (Optional)", 
    placeholder="Enter your Pipedream Notion URL")

# Quick guide before goal input
st.info("""
**Quick Guide:**
1.  **YouTube and Google Drive are configured in the backend.** A learning path document will be created in the common Google Drive.
2.  Optionally, add your Pipedream Notion URL in the sidebar to also save the path to Notion.
3.  Enter a clear learning goal below. For example:
    - "I want to learn python basics in 3 days"
    - "I want to learn data science basics in 10 days"
""")

# Main content area
st.header("Enter Your Goal")
user_goal = st.text_input("Enter your learning goal:",
                        help="Describe what you want to learn. We'll generate a structured path using YouTube and Google Drive.")

# Progress area
progress_container = st.container()
progress_bar = st.empty()

def update_progress(message: str):
    """Update progress in the Streamlit UI"""
    st.session_state.current_step = message
    
    # Determine section and update progress
    if "Setting up agent with tools" in message:
        section = "Setup"
        st.session_state.progress = 0.1
    elif "Added Google Drive integration" in message or "Added Notion integration" in message:
        section = "Integration"
        st.session_state.progress = 0.2
    elif "Creating AI agent" in message:
        section = "Setup"
        st.session_state.progress = 0.3
    elif "Generating your learning path" in message:
        section = "Generation"
        st.session_state.progress = 0.5
    elif "Learning path generation complete" in message:
        section = "Complete"
        st.session_state.progress = 1.0
        st.session_state.is_generating = False
    else:
        section = st.session_state.last_section or "Progress"
    
    st.session_state.last_section = section
    
    progress_bar.progress(st.session_state.progress)
    
    with progress_container:
        if section != st.session_state.last_section and section != "Complete":
            st.write(f"**{section}**")
        
        if message == "Learning path generation complete!":
            st.success("All steps completed! 🎉")
        else:
            prefix = "✓" if st.session_state.progress >= 0.5 else "→"
            st.write(f"{prefix} {message}")


# Generate Learning Path button
if st.button("Generate Learning Path", type="primary", disabled=st.session_state.is_generating):
    if not user_goal:
        st.warning("Please enter your learning goal.")
    else:
        try:
            st.session_state.is_generating = True
            
            st.session_state.current_step = ""
            st.session_state.progress = 0
            st.session_state.last_section = ""
            
            result = run_agent_sync(
                notion_pipedream_url=notion_pipedream_url if notion_pipedream_url else None,
                user_goal=user_goal,
                progress_callback=update_progress
            )
            
            st.header("Your Learning Path")
            if result and "messages" in result:
                for msg in result["messages"]:
                    st.markdown(f"📚 {msg.content}")
            else:
                st.error("No results were generated. Please try again.")
                st.session_state.is_generating = False
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your backend configuration and try again.")
            st.session_state.is_generating = False