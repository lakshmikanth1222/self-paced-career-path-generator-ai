# utils.py

import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from prompt import user_goal_prompt
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
# --- CORRECTED LINE BELOW ---
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional, Any, Callable
import asyncio
from youtube_tools import search_youtube, create_youtube_playlist, add_videos_to_youtube_playlist

# Load environment variables from .env file
load_dotenv()

cfg = RunnableConfig(recursion_limit=100)

# --- CORRECTED FUNCTION SIGNATURE BELOW ---
def initialize_model() -> ChatGoogleGenerativeAI:
    """Initializes the model using the API key from environment variables."""
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")
    # --- CORRECTED CLASS NAME BELOW ---
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=google_api_key
    )

async def setup_agent_with_tools(
    notion_pipedream_url: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Any:
    """
    Set up the agent with backend-configured YouTube and Drive tools,
    and an optional user-provided Notion tool.
    """
    try:
        if progress_callback:
            progress_callback("Setting up agent with tools... ✅")

        # --- Backend Tools Configuration ---
        # 1. Custom YouTube tools (from youtube_tools.py)
        backend_tools = [search_youtube, create_youtube_playlist, add_videos_to_youtube_playlist]
        if progress_callback:
            progress_callback("Initialized YouTube integration... ✅")

        # 2. Drive MCP tool (from environment variable)
        drive_pipedream_url = os.getenv("DRIVE_PIPEDREAM_URL")
        tools_config = {}
        if drive_pipedream_url:
            tools_config["drive"] = {
                "url": drive_pipedream_url,
                "transport": "streamable_http"
            }
            if progress_callback:
                progress_callback("Added Google Drive integration... ✅")
        else:
            print("Warning: DRIVE_PIPEDREAM_URL not found. Drive tool will be unavailable.")

        # --- Optional Frontend Tool Configuration ---
        # 3. Notion MCP tool (from user input)
        if notion_pipedream_url:
            tools_config["notion"] = {
                "url": notion_pipedream_url,
                "transport": "streamable_http"
            }
            if progress_callback:
                progress_callback("Added Notion integration... ✅")

        # --- Combine All Tools ---
        mcp_tools = []
        if tools_config:
            if progress_callback:
                progress_callback("Initializing MCP client for Drive/Notion... ✅")
            mcp_client = MultiServerMCPClient(tools_config)
            mcp_tools = await mcp_client.get_tools()

        all_tools = backend_tools + mcp_tools
        
        if progress_callback:
            progress_callback("Creating AI agent... ✅")
        
        # Initialize model using the backend key
        mcp_orch_model = initialize_model()
        agent = create_react_agent(mcp_orch_model, all_tools)
        
        if progress_callback:
            progress_callback("Setup complete! Starting to generate learning path... ✅")
        
        return agent
    except Exception as e:
        print(f"Error in setup_agent_with_tools: {str(e)}")
        raise

def run_agent_sync(
    notion_pipedream_url: Optional[str] = None,
    user_goal: str = "",
    progress_callback: Optional[Callable[[str], None]] = None
) -> dict:
    """
    Synchronous wrapper for running the agent.
    """
    async def _run():
        try:
            agent = await setup_agent_with_tools(
                notion_pipedream_url=notion_pipedream_url,
                progress_callback=progress_callback
            )
            
            learning_path_prompt = "User Goal: " + user_goal + "\n" + user_goal_prompt
            
            if progress_callback:
                progress_callback("Generating your learning path...")
            
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=learning_path_prompt)]},
                config=cfg
            )
            
            if progress_callback:
                progress_callback("Learning path generation complete!")
            
            return result
        except Exception as e:
            print(f"Error in _run: {str(e)}")
            raise

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
