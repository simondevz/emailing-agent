from pydantic import BaseModel, Field
from typing import TypedDict, Optional, List
from enum import Enum

from langchain.schema.messages import BaseMessage


# --- Enums ---
class DecisionAction(str, Enum):
    ASK_USER = "ask_user"
    PROCEED = "proceed"
    FINALIZE = "finalize"
    ERROR = "error"

class PlaywrightAction(BaseModel):
    type: str = Field(description="Action type: click, fill, type, press, wait, screenshot")
    selector: Optional[str] = Field(None, description="CSS selector for the element")
    value: Optional[str] = Field(None, description="Value for fill, type, press, or wait actions")
    step: Optional[str] = Field(None, description="Step identifier for screenshots")

class PlannerDecision(BaseModel):
    action: DecisionAction = Field(description="Action to take")
    instruction: Optional[PlaywrightAction] = Field(None, description="Playwright action details for 'proceed'")
    message: str = Field(description="Explanation or question for user")
    
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


class PlannerState(BaseModel):
    messages: List[BaseMessage] = Field(default_factory=list)
    email_details: Optional[EmailDetails] = None
    status: str = Field(..., description="collecting | planning | executing | done | error")
    question_to_ask: Optional[str] = None
    current_plan: Optional[List[str]] = Field(default_factory=list)
    current_step: Optional[str] = None
    current_dom: Optional[str] = None
    current_instruction: Optional[str] = None
    execution_result: Optional[str] = None
    ready_for_planner: bool = Field(default=False)
    need_user_input: bool = Field(default=False)
    done: bool = Field(default=False)
    exit_requested: bool = Field(default=False)
    result: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True  # needed for BaseMessage objects
