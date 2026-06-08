from datetime import datetime, timezone
from services.mongodb_client import get_collection


def get_history(session_id: str, limit: int = 10) -> list:
    """
    Fetch the last `limit` messages for a given session_id.
    Returns a list of {"role": ..., "content": ...} dicts
    ready to be passed directly into the agent's messages list.

    Returns empty list if session doesn't exist yet (new conversation).
    """
    collection = get_collection("conversations")
    doc = collection.find_one({"_id": session_id})

    if not doc or not doc.get("messages"):
        return []

    messages = doc["messages"]
    # Return only the last N messages to avoid context window overflow
    return [
        {"role": m["role"], "content": m["content"]}
        for m in messages[-limit:]
    ]


def save_turn(session_id: str, user_message: str, assistant_answer: str):
    """
    Append the user message and assistant answer to the session.
    Creates the session document if it doesn't exist (upsert).

    Each session document looks like:
    {
        "_id": "session-uuid",
        "messages": [
            {"role": "user", "content": "...", "timestamp": ...},
            {"role": "assistant", "content": "...", "timestamp": ...},
            ...
        ],
        "created_at": ...,
        "last_active": ...
    }
    """
    collection = get_collection("conversations")
    now = datetime.now(timezone.utc)

    new_messages = [
        {"role": "user",      "content": user_message,     "timestamp": now},
        {"role": "assistant", "content": assistant_answer,  "timestamp": now},
    ]

    collection.update_one(
        {"_id": session_id},
        {
            "$push": {"messages": {"$each": new_messages}},
            "$set":  {"last_active": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True  # creates document if session doesn't exist
    )