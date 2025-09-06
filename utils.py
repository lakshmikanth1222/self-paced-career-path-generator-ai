
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from prompt import user_goal_prompt
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional, Tuple, Any, Callable
import asyncio
import os

# Backend configuration - Moved from frontend to here
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyAca-e1IA7RHSBncNv3pMoCVneMG1Kk3aI")
YOUTUBE_PIPEDREAM_URL = os.environ.get("YOUTUBE_PIPEDREAM_URL", "https://mcp.pipedream.net/d791e603-ff8e-4364-99ac-da419ec1268a/youtube_data_api")
DRIVE_PIPEDREAM_URL = os.environ.get("DRIVE_PIPEDREAM_URL", "https://mcp.pipedream.net/d791e603-ff8e-4364-99ac-da419ec1268a/google_drive")

cfg = RunnableConfig(recursion_limit=100)

def initialize_model() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GOOGLE_API_KEY
    )

async def setup_agent_with_tools(
    notion_pipedream_url: Optional[str] = None,
    progress_callback: Optional[Callable[[str], None]] = None
) -> Any:
    """
    Set up the agent with YouTube (mandatory), Drive (mandatory), and optional Notion tools.
    """
    try:
        if progress_callback:
            progress_callback("Setting up agent with tools... ✅")
        
        # Initialize tools configuration with mandatory YouTube and Drive
        tools_config = {
            "youtube": {
                "url": YOUTUBE_PIPEDREAM_URL,
                "transport": "streamable_http"
            },
            "drive": {
                "url": DRIVE_PIPEDREAM_URL,
                "transport": "streamable_http"
            }
        }

        if progress_callback:
            progress_callback("Added YouTube integration... ✅")
            progress_callback("Added Google Drive integration... ✅")

        # Add Notion if URL provided
        if notion_pipedream_url:
            tools_config["notion"] = {
                "url": notion_pipedream_url,
                "transport": "streamable_http"
            }
            if progress_callback:
                progress_callback("Added Notion integration... ✅")

        if progress_callback:
            progress_callback("Initializing MCP client... ✅")
        # Initialize MCP client with configured tools
        mcp_client = MultiServerMCPClient(tools_config)
        
        if progress_callback:
            progress_callback("Getting available tools... ✅")
        # Get all tools
        tools = await mcp_client.get_tools()
        
        if progress_callback:
            progress_callback("Creating AI agent... ✅")
        # Create agent with initialized model
        mcp_orch_model = initialize_model()
        agent = create_react_agent(mcp_orch_model, tools)
        
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
            
            # Combine user goal with prompt template
            learning_path_prompt = "User Goal: " + user_goal + "\n" + user_goal_prompt
            
            if progress_callback:
                progress_callback("Generating your learning path...")
            
            # Run the agent
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

    # Run in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
