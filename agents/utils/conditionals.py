from agents.utils.models import AgentState
from rich.console import Console

console = Console()

def decide_after_user_input(state: AgentState) -> str:
    """
    Decide what to do after processing user input.
    """
    if state['exit_requested']:
        return 'end'
    elif state['ready_for_planner']:
        return 'planner_decision'
    else:
        return 'user_agent_decision'

def decide_after_user_agent_decision(state: AgentState) -> str:
    if state['exit_requested'] or state['done']:
        return 'end'
    elif state['need_user_input']:
        return 'user_input'
    elif state['ready_for_planner']:
        return 'planner_decision'
    else:
        return 'user_input'

def decide_after_planner(state: AgentState) -> str:
    if state['exit_requested'] or state['done']:
        return 'end'
    elif state['need_user_input']:
        return 'user_input'
    elif state['status'] == 'executing':
        return 'playwright_execution'
    else:
        return 'planner_decision'  # Loop if needed

def decide_after_playwright(state: AgentState) -> str:
    if state['exit_requested'] or state['done']:
        return 'end'
    else:
        return 'planner_decision'  # Always back to planner after execution

def should_continue(state: AgentState) -> str:
    """Final conditional to continue or end."""
    if state["exit_requested"] or state["done"]:
        console.print(f"\n📋 Final Status: {state['status']}", style="bold yellow")
        if state["done"]:
            console.print("✅ Email task completed!", style="bold green")
            console.print(f"Result: {state['result']}", style="bold green")
        else:
            console.print("⚠️ Task incomplete", style="bold yellow")
        return "end"
    else:
        # This shouldn't be reached, but fallback
        return "user_input"
