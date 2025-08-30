from typing import TypedDict, List, Dict, Optional
from typing_extensions import Annotated

class AgentState(TypedDict):
    user_id: str
    messages: Annotated[List[Dict], "List of chat messages"]
    context: Annotated[Dict, "Context from vector store"]
    requires_confirmation: bool
    confirmation_data: Optional[Dict]
    agent_type: str