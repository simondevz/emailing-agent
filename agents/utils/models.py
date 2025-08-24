from pydantic import BaseModel
from typing import TypedDict, Optional, List
from enum import Enum

from langchain.schema.messages import BaseMessage


# --- Enums ---
class DecisionAction(str, Enum):
    ASK_USER = "ask_user"
    PROCEED = "proceed"
    FINALIZE = "finalize"
    ERROR = "error"

class PlannerDecision(BaseModel):
    action: str  # e.g., "execute", "ask_user", "finalize"
    instruction: Optional[str] = None  # For playwright if "execute"
    message: str  # Explanation or question

# --- Data Models ---
class EmailDetails(BaseModel):
    recipient: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    attachments: Optional[List[str]] = None
    priority: Optional[str] = "normal"

class UserAgentDecision(BaseModel):
    action: DecisionAction
    message: str

# --- Main State ---
class AgentState(TypedDict):
    messages: List[BaseMessage]
    email_details: Optional[EmailDetails]
    status: str  # collecting | planning | executing | done | error
    question_to_ask: Optional[str]
    current_plan: Optional[List[str]]
    current_step: Optional[str]
    current_dom: Optional[str]
    current_instruction: Optional[str]
    execution_result: Optional[str]
    ready_for_planner: bool
    need_user_input: bool
    done: bool
    exit_requested: bool
    result: Optional[str]
    error_message: Optional[str]
