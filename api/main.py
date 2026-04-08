import json
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from orchestrator import Orchestrator
from responder import CitationOutput, TextOutput
from tools import registry

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Lorcana Rules API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

_orchestrator = Orchestrator(registry)


class ChatRequest(BaseModel):
    query: str


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
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
