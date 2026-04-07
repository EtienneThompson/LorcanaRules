import json
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llm import AzureOpenAIClient
from orchestrator import Orchestrator
from responder import TextOutput
from tools import SearchCardsTool, SearchRulesTool, registry

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Lorcana Rules API")

_orchestrator = Orchestrator(registry)


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
async def search_rules(req: SearchRequest):
    logging.info("search_rules called")
    results = await SearchRulesTool().execute(query=req.query, top=req.top)
    return {"query": req.query, "count": len(results), "results": [r.model_dump(mode="json") for r in results]}


@app.post("/search_cards")
async def search_cards(req: SearchRequest):
    logging.info("search_cards called")
    results = await SearchCardsTool().execute(query=req.query, top=req.top)
    return {"query": req.query, "count": len(results), "results": [r.model_dump(mode="json") for r in results]}


# --------------------------------------------------------------------------- #
# Planner endpoints                                                             #
# --------------------------------------------------------------------------- #

@app.post("/plan")
async def plan(req: PlanRequest):
    """
    Run the full RAG pipeline for the user's query and stream back the response.

    The planner, tool executor, and responder are coordinated by the orchestrator.
    Each text chunk is streamed back as a server-sent event as soon as it arrives
    from the responder.
    """
    logging.info("plan called with query: %r", req.query)

    async def generate():
        async for output in _orchestrator.orchestrate(req.query):
            if isinstance(output, TextOutput):
                yield f"data: {json.dumps({'text': output.text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# --------------------------------------------------------------------------- #
# Chat endpoints                                                                #
# --------------------------------------------------------------------------- #

@app.post("/chat")
async def chat(req: ChatRequest):
    logging.info("chat called")
    if not req.messages:
        raise HTTPException(status_code=400, detail="'messages' must be a non-empty list")
    reply = await AzureOpenAIClient().complete(messages=req.messages)
    return {"reply": reply}


@app.post("/chat_stream")
async def chat_stream(req: ChatRequest):
    logging.info("chat_stream called")
    if not req.messages:
        raise HTTPException(status_code=400, detail="'messages' must be a non-empty list")

    async def generate():
        async for chunk in AzureOpenAIClient().stream(messages=req.messages):
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
