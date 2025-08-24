from langchain.schema.messages import SystemMessage, AIMessage
from rich.console import Console
from agents.actions.playwright_execution import PlaywrightAgent
from agents.utils.initializer import get_llm
from agents.utils.models import AgentState, EmailDetails, PlannerDecision, DecisionAction
from agents.utils.prompts import planner_prompt
import json
import traceback

console = Console()
llm = get_llm()

async def generate_planner_decision(state: AgentState, playwright_agent: PlaywrightAgent) -> AgentState:
    """Planner: Generate next step based on objective and current state."""
    if state["exit_requested"] or not state["ready_for_planner"]:
        return state
    
    # Ensure Playwright is initialized
    if not playwright_agent.initialized:
        try:
            if not await playwright_agent.initialize():
                console.print("[bold red]❌ Failed to initialize PlaywrightAgent[/bold red]")
                state["error_message"] = "Failed to initialize PlaywrightAgent"
                state["status"] = "error"
                state["question_to_ask"] = "The email client page failed to load. Please ensure you're logged in and try again."
                state["need_user_input"] = True
                return state
        except Exception as e:
            console.print(f"[bold red]❌ Playwright initialization error: {e}[/bold red]")
            state["error_message"] = f"Playwright initialization error: {str(e)}"
            state["status"] = "error"
            state["question_to_ask"] = "The email client page failed to load. Please ensure you're logged in and try again."
            state["need_user_input"] = True
            return state

    # Ensure we have a DOM snapshot
    if not state["current_dom"]:
        try:
            state["current_dom"] = await playwright_agent.executor.get_dom()
            if state["current_dom"].startswith("Error:"):
                console.print(f"[bold red]❌ DOM fetch error: {state['current_dom']}[/bold red]")
                state["error_message"] = state["current_dom"]
                state["status"] = "error"
                state["question_to_ask"] = "The email client page failed to load. Please ensure you're logged in and try again."
                state["need_user_input"] = True
                return state
        except Exception as e:
            console.print(f"[bold red]❌ Failed to fetch DOM snapshot: {e}[/bold red]")
            state["error_message"] = f"Failed to fetch DOM snapshot: {str(e)}"
            state["status"] = "error"
            state["question_to_ask"] = "The email client page failed to load. Please ensure you're logged in and try again."
            state["need_user_input"] = True
            return state

    console.print(f"🧠 Planning with current DOM: {state['current_dom'][:100] if state['current_dom'] else 'None'}...", style="bold magenta")

    try:
        planner_structured_llm = llm.with_structured_output(PlannerDecision)
        email_details = state.get("email_details")

        # Convert email_details to EmailDetails object if it's a dict, handle None case
        if isinstance(email_details, dict):
            email_details = EmailDetails(**email_details)
        elif email_details is None:
            email_details = EmailDetails()

        objective_json = email_details.model_dump_json() if email_details else "{}"
        
        # Convert previous_steps to a string
        previous_steps = state.get("current_plan", []) or []
        previous_steps_str = json.dumps(previous_steps) if previous_steps else "[]"

        # Debug: Log prompt inputs
        console.print(f"[debug] objective: {objective_json[:100]}...")
        console.print(f"[debug] current_dom: {state['current_dom'][:100]}...")
        console.print(f"[debug] previous_steps: {previous_steps_str[:100]}...")

        # Format the prompt
        prompt_content = planner_prompt.format(
            objective=objective_json,
            current_dom=state["current_dom"],
            previous_steps=previous_steps_str
        )

        decision = planner_structured_llm.invoke([
            SystemMessage(content=prompt_content)
        ] + state["messages"])
        
        console.print(f"📝 Planner Decision: {decision.action} - {decision.message}", style="bold magenta")
        
        state["messages"].append(AIMessage(content=decision.message))
        
        if decision.action == DecisionAction.PROCEED:
            state["current_instruction"] = decision.instruction.dict() if decision.instruction else None
            state["status"] = "executing"
            if decision.instruction:
                state["current_plan"] = state["current_plan"] or []
                state["current_plan"].append(decision.instruction.json())
        elif decision.action == DecisionAction.ASK_USER:
            state["question_to_ask"] = decision.message
            state["need_user_input"] = True
            state["status"] = "collecting"
        elif decision.action == DecisionAction.FINALIZE:
            state["status"] = "done"
            state["done"] = True
            state["result"] = decision.message
        else:
            state["status"] = "error"
            state["error_message"] = decision.message
        
        return state
    
    except Exception as e:
        console.print(f"[bold red]❌ Error in planner: {e}[/bold red]")
        console.print("[bold red]>>> Exception details:[/bold red]")
        console.print(f"[red]Exception type: {type(e)}[/red]")
        console.print(f"[red]Exception message: {str(e)}[/red]")
        console.print("[red]Stack trace:[/red]")
        traceback.print_exc()
        console.print("[bold red]>>> End of exception details[/bold red]")
        
        state["error_message"] = f"Planner error: {str(e)}"
        state["status"] = "error"
        return state