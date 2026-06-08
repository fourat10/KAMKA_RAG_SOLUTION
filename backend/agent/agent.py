import os
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage

from agent.retriever import make_retrieve_tool
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
- When the user asks to summarize, use the document_id provided in the query context
- You have access to the conversation history — use it to answer follow-up questions
  and maintain context across the conversation
- Never mention internal terms like "chunk", "vector", "namespace",
  "embedding", or "Pinecone" to the user
- Be concise and factual"""


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
    tools = [retrieve_tool, calculator, summarize_tool]

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