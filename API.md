# API Documentation - Kamka

## Base URL

```
http://localhost:8000
```

## Authentication

Currently uses `user_id` header/parameter for document ownership verification.

Future: JWT authentication recommended for production.

## Endpoints

### 1. Health Check

**GET** `/health`

Check if backend is running.

**Response (200 OK):**

```json
{
  "status": "ok"
}
```

---

### 2. Upload Document

**POST** `/api/upload`

Upload a PDF or TXT document for processing.

**Headers:**

```
Content-Type: multipart/form-data
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| file | File | ✓ | PDF or TXT file (max 20MB) |
| user_id | string | ✓ | Unique user identifier |

**Example:**

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf" \
  -F "user_id=user_abc123"
```

**Response (200 OK):**

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "chunk_count": 45,
  "cloudinary_url": "https://res.cloudinary.com/...",
  "uploaded_at": "2024-01-15T10:30:00.000Z"
}
```

**Error Responses:**

| Status | Error                   | Description                 |
| ------ | ----------------------- | --------------------------- |
| 400    | Unsupported file type   | Only PDF and TXT allowed    |
| 400    | File too large          | Maximum 20MB                |
| 400    | user_id cannot be empty | user_id is required         |
| 422    | Could not extract text  | File is empty or unreadable |
| 500    | Ingestion failed        | Processing error            |

---

### 3. Chat with Documents

**POST** `/api/chat`

Query documents and get AI-powered answers with citations.

**Headers:**

```
Content-Type: application/json
```

**Request Body:**

```json
{
  "query": "What does this document say about X?",
  "document_ids": ["doc-id-1", "doc-id-2"],
  "user_id": "user_abc123"
}
```

| Field        | Type     | Required | Description                   |
| ------------ | -------- | -------- | ----------------------------- |
| query        | string   | ✓        | Question to ask (min 1 char)  |
| document_ids | string[] | ✓        | Document IDs to query (min 1) |
| user_id      | string   | ✓        | Unique user identifier        |

**Example:**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic?",
    "document_ids": ["550e8400-e29b-41d4-a716-446655440000"],
    "user_id": "user_abc123"
  }'
```

**Response (200 OK):**

```json
{
  "answer": "The document discusses the history of artificial intelligence, covering foundational concepts, modern applications, and future possibilities. It emphasizes the importance of responsible AI development.",
  "citations": [
    {
      "reference": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "document.pdf",
      "page": 5,
      "chunk_index": 12,
      "excerpt": "Artificial intelligence represents one of the most significant technological advances of our time..."
    }
  ],
  "used_retrieval": true
}
```

**Citation Object:**
| Field | Type | Description |
|-------|------|-------------|
| reference | string | Document ID where text came from |
| filename | string | Original filename |
| page | number \| null | Page number if available |
| chunk_index | number \| null | Index of text chunk |
| excerpt | string | Relevant text excerpt |

**Error Responses:**

| Status | Error                    | Description                 |
| ------ | ------------------------ | --------------------------- |
| 400    | Query cannot be empty    | query is required           |
| 400    | At least one document_id | document_ids array required |
| 400    | user_id cannot be empty  | user_id is required         |
| 403    | Document not found       | User doesn't own document   |
| 500    | Agent failed             | LLM processing error        |

---

## Data Types

### Document

```typescript
interface Document {
  document_id: string; // UUID
  filename: string; // Original filename
  chunk_count: number; // Number of chunks
  cloudinary_url: string; // Cloud storage URL
  uploaded_at: ISO8601; // Upload timestamp
}
```

### Citation

```typescript
interface Citation {
  reference: string; // Document ID
  filename: string; // Filename
  page: number | null; // Page number
  chunk_index: number | null; // Chunk index
  excerpt: string; // Text excerpt
}
```

### ChatResponse

```typescript
interface ChatResponse {
  answer: string; // AI response
  citations: Citation[]; // Source references
  used_retrieval: boolean; // Whether retrieval was used
}
```

---

## Status Codes

| Code | Meaning                              |
| ---- | ------------------------------------ |
| 200  | Success                              |
| 400  | Bad request (validation failed)      |
| 403  | Forbidden (permission denied)        |
| 422  | Unprocessable entity (can't process) |
| 500  | Server error                         |

---

## Rate Limiting

Currently no rate limiting. Recommended for production:

- 10 requests/minute per user_id
- 100MB total storage per user

---

## CORS

Allowed origins for development:

- http://localhost:3000
- http://127.0.0.1:3000
- http://localhost:3001
- http://127.0.0.1:3001

Configure in `main.py` for production domains.

---

## Examples

### Upload and Chat Flow

```python
import requests

API_URL = "http://localhost:8000"
USER_ID = "user_123"

# 1. Upload document
upload_resp = requests.post(
    f"{API_URL}/api/upload",
    files={"file": open("document.pdf", "rb")},
    data={"user_id": USER_ID}
)
doc_id = upload_resp.json()["document_id"]

# 2. Chat with document
chat_resp = requests.post(
    f"{API_URL}/api/chat",
    json={
        "query": "Summarize this document",
        "document_ids": [doc_id],
        "user_id": USER_ID
    }
)

print(chat_resp.json()["answer"])
for citation in chat_resp.json()["citations"]:
    print(f"- {citation['filename']}: {citation['excerpt']}")
```

### JavaScript/TypeScript

```typescript
const API_URL = "http://localhost:8000";
const userId = "user_123";

// Upload
const formData = new FormData();
formData.append("file", file);
formData.append("user_id", userId);

const uploadResp = await fetch(`${API_URL}/api/upload`, {
  method: "POST",
  body: formData,
});
const { document_id } = await uploadResp.json();

// Chat
const chatResp = await fetch(`${API_URL}/api/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "What is this about?",
    document_ids: [document_id],
    user_id: userId,
  }),
});
const { answer, citations } = await chatResp.json();
```

---

## Testing

### Using cURL

```bash
# Test health
curl http://localhost:8000/health

# Upload file
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test.pdf" \
  -F "user_id=test_user"

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"?","document_ids":["id"],"user_id":"user"}'
```

### Using Postman

1. Import the collection (coming soon)
2. Set environment variables:
   - `base_url`: http://localhost:8000
   - `user_id`: test_user
   - `document_id`: [from upload response]
3. Run requests

---

## Performance

| Operation      | Typical Time |
| -------------- | ------------ |
| Upload 5MB PDF | 5-10 seconds |
| Extract text   | 2-3 seconds  |
| Embed chunks   | 1-2 seconds  |
| Chat query     | 3-5 seconds  |

---

## Limits

| Resource               | Limit                   |
| ---------------------- | ----------------------- |
| File size              | 20MB                    |
| Query length           | 5000 chars              |
| Documents per query    | Unlimited               |
| Response tokens        | 2000                    |
| Daily uploads per user | Unlimited (no auth yet) |

---

## Future Enhancements

- [ ] Authentication (JWT)
- [ ] Rate limiting per user
- [ ] Batch operations
- [ ] Document versioning
- [ ] Full-text search
- [ ] WebSocket for real-time chat
- [ ] Export chat history
- [ ] Document sharing
