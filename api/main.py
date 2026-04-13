import asyncio
import json
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from orchestrator import Orchestrator
from responder import CardOutput, CitationOutput, TextOutput
from search import CardsSearch
from tools import registry

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Lorcana Rules API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

_cards_search = CardsSearch()

_orchestrator = Orchestrator(registry)


class ChatRequest(BaseModel):
    query: str


@app.get("/search_cards")
async def search_cards(request: Request, q: str = ""):
    """
    Return cards whose name starts with the given prefix.
    Used by the chat input autocomplete when the user types [[ followed by text.

    If the client disconnects before the search completes (e.g. the user kept
    typing and the frontend cancelled the request) the search task is abandoned
    early and a 499 is returned, freeing resources without waiting for the
    Azure AI Search call to finish.
    """
    if not q:
        return []

    search_task = asyncio.create_task(
        asyncio.to_thread(_cards_search.search_by_name_prefix, q)
    )

    # Poll for client disconnection every 50 ms while the search runs.
    while True:
        done, _ = await asyncio.wait({search_task}, timeout=0.05)
        if done:
            results = search_task.result()
            return [
                {"card_id": r.id, "full_name": r.fullName, "image_url": r.images.thumbnail}
                for r in results
            ]
        if await request.is_disconnected():
            search_task.cancel()
            logging.info("search_cards: client disconnected, abandoned search for q=%r", q)
            return Response(status_code=499)


@app.post("/chat")
async def chat(req: ChatRequest):
    """
    Run the full RAG pipeline for the user's query and stream back the response.

    The planner, tool executor, and responder are coordinated by the orchestrator.
    Each text chunk is streamed back as a server-sent event as soon as it arrives
    from the responder.
    """
    logging.info("chat called with query: %r", req.query)

    async def generate():
        async for output in _orchestrator.orchestrate(req.query):
            if isinstance(output, TextOutput):
                yield f"data: {json.dumps({'type': 'text', 'text': output.text})}\n\n"
            elif isinstance(output, CitationOutput):
                yield f"data: {json.dumps({'type': 'citation', 'number': output.number, 'rule_id': output.rule_id, 'rule_text': output.rule_text})}\n\n"
            elif isinstance(output, CardOutput):
                yield f"data: {json.dumps({'type': 'card', 'card_id': output.card_id, 'full_name': output.full_name, 'image_url': output.image_url})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
