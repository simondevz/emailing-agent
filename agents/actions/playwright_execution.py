from typing import List
from langchain.schema.messages import AIMessage
from rich.console import Console

from agents.utils.initializer import get_llm
from agents.utils.models import AgentState

console = Console()

# llm = get_llm()

def execute_playwright_action(state: AgentState) -> AgentState:
    """Playwright: Execute the instruction and update DOM."""
    if state["exit_requested"] or not state["current_instruction"]:
        return state

    console.print(f"⚙️ Executing instruction: {state['current_instruction']}", style="bold blue")

    try:
        # Assume playwright_prompt and integration: use Playwright library to execute
        # For demo, simulate execution
        # In real: from playwright.sync_api import sync_playwright
        # Execute step, capture new DOM or screenshot/text
        new_dom = "SIMULATED NEW DOM AFTER EXECUTION"  # Replace with actual Playwright call
        execution_result = "Action executed successfully."

        state["current_dom"] = new_dom
        state["execution_result"] = execution_result
        state["status"] = "planning"  # Back to planner
        state["current_instruction"] = None  # Clear after execution

        state["messages"].append(AIMessage(content=f"Executed: {state['current_instruction']}. Result: {execution_result}"))

        return state
    
    except Exception as e:
        console.print(f"❌ Error in playwright execution: {e}", style="bold red")
        state["error_message"] = str(e)
        state["status"] = "error"
        return state
