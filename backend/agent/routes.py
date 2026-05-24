from backend.agent.graph import graph
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from backend.auth.routes import user_dependency, Database
from langchain_core.messages import HumanMessage


class ChatMessage(BaseModel):
    message: str

router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)
@router.post("/ask")
async def ask(chat_request: ChatMessage,
              user: user_dependency,
              db: Database):
    try:
        config = {"configurable": {"thread_id": user["id"]}}
        input_state = {
            "messages": [HumanMessage(content=chat_request.message)],
            "user_query": chat_request.message,
        }

        result = graph.invoke(input_state, config=config)

        return result.get("response")
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Error has occured to the chatbot") from exc