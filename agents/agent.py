import asyncio
from langgraph.graph import StateGraph, END, START
from agents.actions.playwright_execution import execute_playwright_action, PlaywrightAgent
from agents.actions.planning import generate_planner_decision
from agents.actions.user_interaction import initialize_state, process_user_input, generate_user_agent_decision
from agents.utils.conditionals import decide_after_planner, decide_after_playwright, decide_after_user_agent_decision, decide_after_user_input
from agents.utils.models import AgentState, PlannerState
from rich.console import Console

console = Console()

def sync_generate_planner_decision(state: dict, playwright_agent: PlaywrightAgent):
    try:
        # Validate the state
        validated_state = PlannerState.model_validate(state)
        print("State validated successfully.")
        print("Validated State:", validated_state)
    except Exception as e:
        print("State validation failed:", e)
        raise

    return asyncio.run(generate_planner_decision(validated_state.model_dump(), playwright_agent))

def sync_execute_playwright_action(state, playwright_agent):
    return asyncio.run(execute_playwright_action(state, playwright_agent))

def create_email_agent(provider: str = "gmail"):
    """Create the full email agent graph."""
    # Initialize PlaywrightAgent
    playwright_agent = PlaywrightAgent(provider)
    
    # Build the graph
    graph = StateGraph(AgentState)

    # Add nodes with PlaywrightAgent
    graph.add_node("initialize", initialize_state)
    graph.add_node("user_input", process_user_input)
    graph.add_node("user_agent_decision", generate_user_agent_decision)
    graph.add_node("planner_decision", lambda state: sync_generate_planner_decision(state, playwright_agent))
    graph.add_node("playwright_execution", lambda state: sync_execute_playwright_action(state, playwright_agent))


    # Add edges
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "user_input")

    # Conditional edges
    graph.add_conditional_edges(
        "user_input",
        decide_after_user_input,
        {
            "user_agent_decision": "user_agent_decision",
            "planner_decision": "planner_decision",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "user_agent_decision",
        decide_after_user_agent_decision,
        {
            "user_input": "user_input",
            "planner_decision": "planner_decision",
            "end": END,
        },
    )

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

    graph.add_conditional_edges(
        "playwright_execution",
        decide_after_playwright,
        {
            "planner_decision": "planner_decision",
            "end": END,
        },
    )

    # Compile the graph with cleanup
    async def cleanup():
        await playwright_agent.cleanup()

    app = graph.compile()
    app.cleanup = cleanup  # Attach cleanup method
    return app

async def run_email_agent(provider: str = "gmail"):
    """Run the email agent with CLI interaction."""
    console.print("🤖 Full Email Agent CLI", style="bold blue")
    console.print("=" * 40, style="dim")
    
    try:
        app = create_email_agent(provider)
        await app.ainvoke({})
        console.print("\n🏁 Agent execution completed.", style="bold green")
    except KeyboardInterrupt:
        console.print("\n⚠️ Process interrupted by user", style="bold yellow")
    except Exception as e:
        console.print(f"❌ Error occurred: {e}", style="bold red")
        import traceback
        traceback.print_exc()
    finally:
        await app.cleanup()