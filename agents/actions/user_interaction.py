from typing import List
from langchain.schema.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from rich.console import Console
from rich.prompt import Prompt

from agents.utils.initializer import get_llm
from agents.utils.models import AgentState, DecisionAction, EmailDetails, UserAgentDecision
from agents.utils.prompts import user_agent_prompt

console = Console()

llm = get_llm()

def initialize_state(state: AgentState) -> AgentState:
    """Initialize the agent state."""
    state["messages"] = []
    state["email_details"] = None
    state["status"] = "collecting"
    state["question_to_ask"] = None
    state["current_plan"] = None
    state["current_step"] = None
    state["current_dom"] = None
    state["current_instruction"] = None
    state["execution_result"] = None
    state["ready_for_planner"] = False
    state["need_user_input"] = False
    state["done"] = False
    state["exit_requested"] = False
    state["result"] = None
    state["error_message"] = None
    return state

def process_user_input(state: AgentState) -> AgentState:
    """Process user input and add it to the messages."""
    try:
        # Determine prompt
        if state["question_to_ask"]:
            prompt_text = state["question_to_ask"]
        else:
            prompt_text = "📧 What would you like to do with emailBot? "

        # Get user input with Rich Prompt
        user_input = Prompt.ask(f"\n[bold cyan]{prompt_text}[/bold cyan]")

        # Check for exit command
        if user_input.lower() in ["exit", "quit", "bye"]:
            state["exit_requested"] = True
            return state

        # Add user message to the conversation history (only for non-commands)
        if user_input.strip():  # Ensure we don't add empty messages
            state["messages"].append(HumanMessage(content=user_input))

        # Clear the question after use
        state["question_to_ask"] = None
        state["need_user_input"] = False

        return state

    except KeyboardInterrupt:
        state["exit_requested"] = True
        return state
    except Exception as e:
        console.print(f"❌ Error processing input: {e}", style="bold red")
        return state

def generate_user_agent_decision(state: AgentState) -> AgentState:
    """Generate user agent decision using the LLM."""
    # Skip if exit requested or no messages
    if state["exit_requested"] or not state["messages"]:
        return state

    # Also skip if the last message is not from user
    if state["messages"][-1].type != "human":
        return state

    console.print(f"📨 Processing messages: {len(state['messages'])} total", style="bold yellow")
    console.print(f"📊 Current status: {state['status']}", style="bold yellow")

    try:
        # Create a simple, clean prompt for structured output
        decision_prompt = f"""
{user_agent_prompt}

Current conversation context: The user wants help with email tasks.

Based on the messages, decide what to do:
1. "ask_user" - Need more information from user
2. "proceed" - Have enough info to proceed 
3. "finalize" - Task is complete

Keep your message simple and clear without special formatting.
"""

        # Get decision from LLM
        structured_llm = llm.with_structured_output(UserAgentDecision)
        
        decision = structured_llm.invoke([
            SystemMessage(content=decision_prompt)
        ] + state["messages"])
        
        console.print(f"🤖 UserAgent Decision: {decision.action} - {decision.message}", style="bold green")
        
        # Handle different actions
        if decision.action == DecisionAction.ASK_USER:
            # Set question to ask user
            state["question_to_ask"] = decision.message
            state["messages"].append(AIMessage(content=decision.message))
            state["status"] = "collecting"
            state["need_user_input"] = True
            return state
        
        elif decision.action == DecisionAction.PROCEED:
            # Extract email details from the conversation
            email_details = extract_email_details_from_messages(state["messages"])
            
            console.print(f"✅ Extracted email details: {email_details}", style="bold green")
            
            state["messages"].append(AIMessage(content="Great! I have the information needed. Ready to proceed with planning."))
            state["email_details"] = email_details
            state["status"] = "planning"
            state["ready_for_planner"] = True
            state["done"] = False
            return state
            
        elif decision.action == DecisionAction.FINALIZE:
            state["messages"].append(AIMessage(content=decision.message))
            state["status"] = "done"
            state["done"] = True
            state["result"] = "Task completed successfully"
            return state
        
        else:  # ERROR case
            state["messages"].append(AIMessage(content="I encountered an error processing your request."))
            state["status"] = "error"
            state["done"] = True
            state["error_message"] = decision.message
            return state
            
    except Exception as e:
        console.print(f"❌ Error in generate_user_agent_decision: {e}", style="bold red")
        state["question_to_ask"] = "I had trouble understanding your request. Could you please clarify what you'd like to do with email?"
        state["status"] = "collecting"
        state["need_user_input"] = True
        state["error_message"] = str(e)
        return state

def extract_email_details_from_messages(messages: List[BaseMessage]) -> EmailDetails:
    """
    Extract email details from the conversation messages.
    This could use an LLM or simple parsing.
    """
    
    # Simple approach: use LLM to extract structured info
    try:
        extractor_llm = llm.with_structured_output(EmailDetails)
        
        extraction_prompt = """
Extract email details from this conversation.
Look for:
- Recipient name/email
- Subject line
- Message body/content  
- Any attachments mentioned
- Priority level

If information is not mentioned, leave fields as null.
"""
        
        email_details = extractor_llm.invoke([
            SystemMessage(content=extraction_prompt)
        ] + messages)
        
        return email_details
        
    except Exception as e:
        console.print(f"⚠️ Could not extract email details: {e}", style="bold yellow")
        # Return empty details if extraction fails
        return EmailDetails()
