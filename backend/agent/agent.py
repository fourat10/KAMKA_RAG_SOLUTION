import os
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

from agent.retriever import make_retrieve_tool
from agent.document_lookup_tool import make_document_lookup_tool
from agent.calculator_tool import calculator
from agent.summarize_tool import make_summarize_tool
from agent.citation_parser import parse_citations


def get_model():
    """
    Initializes the LLM via OpenRouter.
    OpenRouter is OpenAI-compatible — we use model_provider="openai"
    and override base_url to point to OpenRouter's API endpoint.
    """
    return init_chat_model(
        model=os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free"),
        model_provider="openai",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
    )


SYSTEM_PROMPT = """You are a document assistant. You help users understand, query,
and extract information from their uploaded documents.

You have access to three tools:
- retrieve_context: search document content for specific information
- calculator: evaluate mathematical expressions
- summarize_document: fetch and summarize a full document
- document_lookup: find the document_id for a filename the user mentioned

Important rules:
- Always use retrieve_context when the question is about document content
- Always use calculator when the user asks to compute numbers
- Always use summarize_document when the user asks for a summary or overview of a document
- For greetings or simple conversation (Hello, Thanks, How are you),
  answer directly without using any tool
- When using retrieve_context, always cite sources as [1], [2]... inline in your answer
- If retrieve_context returns no relevant information, say clearly:
  "I couldn't find information about this in the selected documents."
  Never make up or guess information that isn't in the documents
- When the user mentions a filename (e.g. "summarize file1.txt"), always call document_lookup first to get the correct document_id, then call summarize_document with that ID
- You have access to the conversation history — use it to answer follow-up questions
  and maintain context across the conversation
- Never mention internal terms like "chunk", "vector", "namespace",
  "embedding", or "Pinecone" to the user
- Never mention document IDs (UUIDs) in your responses to the user
- Be concise and factual
- Never use tables, graphs, or markdown formatting in your responses — use plain text and bullet points only"""


def run_agent(
    query: str,
    document_ids: list[str],
    history: list[dict] | None = None,
) -> dict:
    """
    Runs the LangChain agent with conversation history support.

    Args:
        query: the enriched user query (with document_ids injected by chat.py)
        document_ids: list of document IDs selected by the user
        history: list of previous messages from MongoDB
                 [{"role": "user", "content": "..."}, ...]

    Returns:
        {
            "answer": the LLM's final answer string,
            "citations": list of structured citation objects
        }
    """
    model = get_model()

    # Build scoped tools — document_ids locked in via closure
    retrieve_tool = make_retrieve_tool(document_ids)
    summarize_tool = make_summarize_tool(document_ids)
    lookup_tool = make_document_lookup_tool(document_ids)
    tools = [retrieve_tool, calculator, summarize_tool, lookup_tool]

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    # Convert history dicts to LangChain message objects
    # LangGraph's create_agent requires HumanMessage/AIMessage objects
    # not plain {"role": ..., "content": ...} dicts for history
    if history is None:
        history = []

    message_objects = []
    for msg in history:
        if msg["role"] == "user":
            message_objects.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            message_objects.append(AIMessage(content=msg["content"]))

    # Add the current query as the final HumanMessage
    message_objects.append(HumanMessage(content=query))

    response = agent.invoke({"messages": message_objects})

    # Final answer is the last message in the response
    answer = response["messages"][-1].content

    # Extract retrieved Document objects from ToolMessages for citations
    retrieved_docs = []
    for message in response["messages"]:
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            if isinstance(message.artifact, list):
                retrieved_docs.extend(message.artifact)

    # Build structured citations from real chunk metadata
    citations = parse_citations(answer, retrieved_docs)

    return {
        "answer": answer,
        "citations": citations,
    }


async def run_agent_stream(
    query: str,
    document_ids: list[str],
    history: list[dict] | None = None,
):
    """
    Async generator that:
    1. Runs the full agent (tool calls happen normally)
    2. Streams the final answer token by token using LLM streaming
    3. Yields citations at the end

    Yields dicts:
        {"type": "token",  "content": "word "}  — one per token
        {"type": "done",   "answer": "...", "citations": [...]}  — final event
    """
    from langchain_core.messages import HumanMessage, AIMessage

    model = get_model()

    # Build scoped tools
    retrieve_tool = make_retrieve_tool(document_ids)
    summarize_tool = make_summarize_tool(document_ids)
    lookup_tool = make_document_lookup_tool(document_ids)
    tools = [retrieve_tool, calculator, summarize_tool, lookup_tool]

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

    # Convert history to message objects
    if history is None:
        history = []

    message_objects = []
    for msg in history:
        if msg["role"] == "user":
            message_objects.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            message_objects.append(AIMessage(content=msg["content"]))
    message_objects.append(HumanMessage(content=query))

    # --- Step 1: Run full agent to complete all tool calls ---
    response = agent.invoke({"messages": message_objects})
    answer = response["messages"][-1].content

    # --- Step 2: Extract citations from tool calls ---
    retrieved_docs = []
    for message in response["messages"]:
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            if isinstance(message.artifact, list):
                retrieved_docs.extend(message.artifact)

    citations = parse_citations(answer, retrieved_docs)

    # --- Step 3: Stream the answer token by token ---
    # Stream character by character in small chunks to avoid
    # spacing artifacts that occur when splitting by words
    import asyncio
    chunk_size = 3  # stream 3 characters at a time — smooth but not too slow
    for i in range(0, len(answer), chunk_size):
        yield {"type": "token", "content": answer[i:i + chunk_size]}
        await asyncio.sleep(0.01)

    # --- Step 4: Yield final event with full answer + citations ---
    yield {
        "type": "done",
        "answer": answer,
        "citations": [
            {
                "reference": c["reference"],
                "filename": c["filename"],
                "page": c["page"],
                "chunk_index": c["chunk_index"],
                "excerpt": c["excerpt"],
            }
            for c in citations
        ],
    }