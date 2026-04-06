import json
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llm import AzureOpenAIClient
from planner import Planner
from tools import SearchCardsTool, SearchRulesTool, registry

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Lorcana Rules API")


# --------------------------------------------------------------------------- #
# Request models                                                               #
# --------------------------------------------------------------------------- #

class SearchRequest(BaseModel):
    query: str
    top: int = 5


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]


class PlanRequest(BaseModel):
    query: str


# --------------------------------------------------------------------------- #
# Search endpoints                                                              #
# --------------------------------------------------------------------------- #

@app.post("/search_rules")
def search_rules(req: SearchRequest):
    logging.info("search_rules called")
    results = SearchRulesTool().execute(query=req.query, top=req.top)
    return {"query": req.query, "count": len(results), "results": [r.model_dump(mode="json") for r in results]}


@app.post("/search_cards")
def search_cards(req: SearchRequest):
    logging.info("search_cards called")
    results = SearchCardsTool().execute(query=req.query, top=req.top)
    return {"query": req.query, "count": len(results), "results": [r.model_dump(mode="json") for r in results]}


# --------------------------------------------------------------------------- #
# Planner endpoints                                                             #
# --------------------------------------------------------------------------- #

@app.post("/plan")
def plan(req: PlanRequest):
    """
    Run the planner against the user's query and return the tool calls it chose.

    Useful for testing the planner in isolation before wiring in tool execution
    and the responder.  The response lists each tool call in order, with its
    name and parsed arguments.
    """
    logging.info("plan called with query: %r", req.query)
    tool_calls = list(Planner(tools=registry.TOOLS).plan(req.query))
    return {
        "query": req.query,
        "tool_calls": [
            {"name": tc.name, "arguments": tc.arguments}
            for tc in tool_calls
        ],
    }


# --------------------------------------------------------------------------- #
# Chat endpoints                                                                #
# --------------------------------------------------------------------------- #

@app.post("/chat")
def chat(req: ChatRequest):
    logging.info("chat called")
    if not req.messages:
        raise HTTPException(status_code=400, detail="'messages' must be a non-empty list")
    reply = AzureOpenAIClient().complete(messages=req.messages)
    return {"reply": reply}


@app.post("/chat_stream")
def chat_stream(req: ChatRequest):
    logging.info("chat_stream called")
    if not req.messages:
        raise HTTPException(status_code=400, detail="'messages' must be a non-empty list")

    def generate():
        for chunk in AzureOpenAIClient().stream(messages=req.messages):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
