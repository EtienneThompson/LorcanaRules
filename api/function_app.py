import json
import logging

import azure.functions as func

from llm import AzureOpenAIClient
from search import CardsSearch, RulesSearch

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def _parse_query(req: func.HttpRequest) -> tuple[str | None, int]:
    """Extract search query and optional top-N count from the request."""
    query = req.params.get("query")
    top = req.params.get("top")

    if not query:
        try:
            body = req.get_json()
            query = body.get("query")
            top = top or body.get("top")
        except ValueError:
            pass

    try:
        top = int(top) if top is not None else 5
    except ValueError:
        top = 5

    return query, top


@app.route(route="search_rules", methods=["GET", "POST"])
def search_rules(req: func.HttpRequest) -> func.HttpResponse:
    """Search the rules index. Accepts ?query=<text>&top=<n>."""
    logging.info("search_rules triggered")

    query, top = _parse_query(req)
    if not query:
        return func.HttpResponse(
            json.dumps({"error": "Missing required parameter: query"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        results = RulesSearch().search(query=query, top=top)
        return func.HttpResponse(
            json.dumps({"query": query, "count": len(results), "results": [r.model_dump(mode="json") for r in results]}),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Error searching rules index")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="search_cards", methods=["GET", "POST"])
def search_cards(req: func.HttpRequest) -> func.HttpResponse:
    """Search the cards index. Accepts ?query=<text>&top=<n>."""
    logging.info("search_cards triggered")

    query, top = _parse_query(req)
    if not query:
        return func.HttpResponse(
            json.dumps({"error": "Missing required parameter: query"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        results = CardsSearch().search(query=query, top=top)
        return func.HttpResponse(
            json.dumps({"query": query, "count": len(results), "results": [r.model_dump(mode="json") for r in results]}),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Error searching cards index")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


def _parse_messages(req: func.HttpRequest) -> list[dict[str, str]] | None:
    """Extract the messages list from the request body."""
    try:
        body = req.get_json()
        messages = body.get("messages")
        if isinstance(messages, list) and messages:
            return messages
    except ValueError:
        pass
    return None


def _sse_event(data: str) -> str:
    """Format a string as an SSE data event."""
    return f"data: {data}\n\n"


@app.route(route="chat", methods=["POST"])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    """
    Send a chat completion request and return the full response.

    Request body:
        {
            "messages": [{"role": "user", "content": "..."}]
        }
    """
    logging.info("chat triggered")

    messages = _parse_messages(req)
    if not messages:
        return func.HttpResponse(
            json.dumps({"error": "Request body must include a non-empty 'messages' list"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        reply = AzureOpenAIClient().complete(messages=messages)
        return func.HttpResponse(
            json.dumps({"reply": reply}),
            status_code=200,
            mimetype="application/json",
        )
    except Exception as e:
        logging.exception("Error calling Azure OpenAI")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


@app.route(route="chat_stream", methods=["POST"])
def chat_stream(req: func.HttpRequest) -> func.HttpResponse:
    """
    Send a chat completion request and stream the response as SSE events.

    Each chunk is sent as:
        data: <text delta>\\n\\n

    A final sentinel event signals completion:
        data: [DONE]\\n\\n

    Request body:
        {
            "messages": [{"role": "user", "content": "..."}]
        }
    """
    logging.info("chat_stream triggered")

    messages = _parse_messages(req)
    if not messages:
        return func.HttpResponse(
            json.dumps({"error": "Request body must include a non-empty 'messages' list"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        def generate():
            for chunk in AzureOpenAIClient().stream(messages=messages):
                yield _sse_event(json.dumps({"chunk": chunk}))
            yield _sse_event("[DONE]")

        return func.HttpResponse(
            body=generate(),
            status_code=200,
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logging.exception("Error streaming Azure OpenAI response")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
