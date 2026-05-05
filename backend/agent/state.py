from typing import Sequence, TypedDict, Annotated, Optional, Dict, List, Any
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    user_query: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    intent: Optional[str]
    inputs: Annotated[Dict[str, Any], operator.ior]
    missing_fields: Annotated[List[str], operator.add]
    data: Annotated[Dict[str, Any], operator.ior]
    response: Optional[Dict[str, Any]]