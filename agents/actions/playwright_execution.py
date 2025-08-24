from typing import Dict, Any
from rich.console import Console
from agents.utils.models import AgentState
from langchain.schema.messages import AIMessage

from agents.utils.tools import PlaywrightExecutor

console = Console()

class PlaywrightAgent:
    def __init__(self, provider: str = "gmail"):
        self.executor = PlaywrightExecutor(provider)
        self.initialized = False

    async def initialize(self):
        """Initialize the Playwright executor"""
        if not self.initialized:
            self.initialized = await self.executor.setup()
        return self.initialized

    async def cleanup(self):
        """Clean up the Playwright executor"""
        await self.executor.cleanup()

async def execute_playwright_action(state: AgentState, playwright_agent: PlaywrightAgent) -> AgentState:
    """Execute Playwright action asynchronously"""
    if state["exit_requested"] or not state["current_instruction"]:
        return state

    console.print(f"⚙️ Executing instruction: {state['current_instruction']}", style="bold blue")

    try:
        # Ensure Playwright is initialized
        if not playwright_agent.initialized:
            if not await playwright_agent.initialize():
                state["error_message"] = "Failed to initialize Playwright"
                state["status"] = "error"
                return state

        # Execute action
        result = await playwright_agent.executor.execute_action(state["current_instruction"])
        
        if result["success"]:
            # Update DOM after action
            new_dom = await playwright_agent.executor.get_dom()
            state["current_dom"] = new_dom
            state["execution_result"] = result["action"]
            state["status"] = "planning"
            state["messages"].append(AIMessage(content=f"Executed: {result['action']}"))
        else:
            state["error_message"] = result["error"]
            state["status"] = "error"
            state["messages"].append(AIMessage(content=f"Execution failed: {result['error']}"))
        
        state["current_instruction"] = None
        return state
    
    except Exception as e:
        console.print(f"❌ Error in Playwright execution: {e}", style="bold red")
        state["error_message"] = str(e)
        state["status"] = "error"
        state["messages"].append(AIMessage(content=f"Execution failed: {str(e)}"))
        return state