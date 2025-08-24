from rich.console import Console
from langgraph.graph import StateGraph, END, START

from agents.actions.playwright_execution import execute_playwright_action
from agents.actions.planning import generate_planner_decision
from agents.actions.user_interaction import initialize_state, process_user_input, generate_user_agent_decision
from agents.utils.conditionals import decide_after_planner, decide_after_playwright, decide_after_user_agent_decision, decide_after_user_input
from agents.utils.models import AgentState


console = Console()

def create_email_agent():
    """Create the full email agent graph."""
    
    # Build the graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("initialize", initialize_state)
    graph.add_node("user_input", process_user_input)
    graph.add_node("user_agent_decision", generate_user_agent_decision)
    graph.add_node("planner_decision", generate_planner_decision)
    graph.add_node("playwright_execution", execute_playwright_action)

    # Add edges
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "user_input")

    # After user_input
    graph.add_conditional_edges(
        "user_input",
        decide_after_user_input,
        {
            "user_agent_decision": "user_agent_decision",
            "planner_decision": "planner_decision",
            "end": END,
        },
    )

    # After user_agent_decision
    graph.add_conditional_edges(
        "user_agent_decision",
        decide_after_user_agent_decision,
        {
            "user_input": "user_input",
            "planner_decision": "planner_decision",
            "end": END,
        },
    )

    # After planner_decision
    graph.add_conditional_edges(
        "planner_decision",
        decide_after_planner,
        {
            "user_input": "user_input",
            "playwright_execution": "playwright_execution",
            "planner_decision": "planner_decision",
            "end": END,
        },
    )

    # After playwright_execution
    graph.add_conditional_edges(
        "playwright_execution",
        decide_after_playwright,
        {
            "planner_decision": "planner_decision",
            "end": END,
        },
    )

    # Compile the graph
    app = graph.compile()
    
    return app

def run_email_agent(provider: str = "gmail"):
    """Run the email agent with CLI interaction."""
    
    console.print("🤖 Full Email Agent CLI", style="bold blue")
    console.print("=" * 40, style="dim")
    
    # Create the graph
    app = create_email_agent()
    
    try:
        # Invoke the graph
        app.invoke({})
        
        console.print("\n🏁 Agent execution completed.", style="bold green")
        
    except KeyboardInterrupt:
        console.print("\n⚠️ Process interrupted by user", style="bold yellow")
    except Exception as e:
        console.print(f"❌ Error occurred: {e}", style="bold red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_email_agent()