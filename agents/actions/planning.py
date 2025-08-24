from langchain.schema.messages import SystemMessage, AIMessage
from rich.console import Console

from agents.utils.initializer import get_llm
from agents.utils.models import AgentState, PlannerDecision
from agents.utils.prompts import planner_prompt

console = Console()

llm = get_llm()

def generate_planner_decision(state: AgentState) -> AgentState:
    """Planner: Generate next step based on objective and current state."""
    if state["exit_requested"] or not state["ready_for_planner"]:
        return state

    console.print(f"🧠 Planning with current DOM: {state['current_dom'][:100] if state['current_dom'] else 'None'}...", style="bold magenta")

    try:
        planner_structured_llm = llm.with_structured_output(PlannerDecision)
        
        decision = planner_structured_llm.invoke([
            SystemMessage(content=planner_prompt.format(
                objective=state["email_details"],
                current_dom=state["current_dom"],
                previous_steps=state["current_plan"]
            ))
        ] + state["messages"])
        
        console.print(f"📝 Planner Decision: {decision.action} - {decision.message}", style="bold magenta")
        
        state["messages"].append(AIMessage(content=decision.message))
        
        if decision.action == "execute":
            state["current_instruction"] = decision.instruction
            state["status"] = "executing"
        elif decision.action == "ask_user":
            state["question_to_ask"] = decision.message
            state["need_user_input"] = True
            state["status"] = "collecting"
        elif decision.action == "finalize":
            state["status"] = "done"
            state["done"] = True
            state["result"] = decision.message
        else:
            state["status"] = "error"
            state["error_message"] = decision.message
        
        # Update plan if needed
        if not state["current_plan"]:
            state["current_plan"] = []  # Generate initial plan here if needed
        
        return state
    
    except Exception as e:
        console.print(f"❌ Error in planner: {e}", style="bold red")
        state["error_message"] = str(e)
        state["status"] = "error"
        return state
