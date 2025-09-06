
import streamlit as st
from utils import run_agent_sync

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

# Configuration (moved to backend - only Notion remains optional)
st.sidebar.header("Configuration")

# Secondary tool selection
secondary_tool = st.sidebar.radio(
    "Select Secondary Tool:",
    ["Drive", "Notion"]
)

# Notion URL input (only if Notion is selected)
if secondary_tool == "Notion":
    notion_pipedream_url = st.sidebar.text_input("Notion URL", 
        placeholder="Enter your Pipedream Notion URL")
else:
    notion_pipedream_url = None

# Quick guide before goal input
st.info("""
**Quick Guide:**
1. Select your preferred secondary tool (Drive or Notion)
2. If selecting Notion, enter your Notion Pipedream URL
3. Enter a clear learning goal, for example:
    - "I want to learn python basics in 3 days"
    - "I want to learn data science basics in 10 days"
""")

# Main content area
st.header("Enter Your Goal")
user_goal = st.text_input("Enter your learning goal:",
                        help="Describe what you want to learn, and we'll generate a structured path using YouTube content and your selected tool.")

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
    
    # Show progress bar
    progress_bar.progress(st.session_state.progress)
    
    # Update progress container with current status
    with progress_container:
        # Show section header if it changed
        if section != st.session_state.last_section and section != "Complete":
            st.write(f"**{section}**")
        
        # Show message with tick for completed steps
        if message == "Learning path generation complete!":
            st.success("All steps completed! 🎉")
        else:
            prefix = "✓" if st.session_state.progress >= 0.5 else "→"
            st.write(f"{prefix} {message}")

# Generate Learning Path button
if st.button("Generate Learning Path", type="primary", disabled=st.session_state.is_generating):
    if (secondary_tool == "Notion" and not notion_pipedream_url):
        st.error(f"Please enter your Pipedream Notion URL in the sidebar.")
    elif not user_goal:
        st.warning("Please enter your learning goal.")
    else:
        try:
            # Set generating flag
            st.session_state.is_generating = True
            
            # Reset progress
            st.session_state.current_step = ""
            st.session_state.progress = 0
            st.session_state.last_section = ""
            
            result = run_agent_sync(
                notion_pipedream_url=notion_pipedream_url,
                user_goal=user_goal,
                progress_callback=update_progress
            )
            
            # Display results
            st.header("Your Learning Path")
            if result and "messages" in result:
                for msg in result["messages"]:
                    st.markdown(f"📚 {msg.content}")
            else:
                st.error("No results were generated. Please try again.")
                st.session_state.is_generating = False
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your configuration and try again.")
            st.session_state.is_generating = False
