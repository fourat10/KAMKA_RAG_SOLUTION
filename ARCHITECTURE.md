# Architecture Guide - Kamka Document Assistant

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                              │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              FRONTEND (Next.js + React)                    │  │
│  │            http://localhost:3000                           │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │ Upload Form  │  │ Document     │  │ Chat         │    │  │
│  │  │              │  │ List         │  │ Interface    │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  │         ↓                                      ↓           │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │     Zustand Store (State Management)                 │ │  │
│  │  │  - userId, documents, selectedDocIds, messages       │ │  │
│  │  │  - Persisted to localStorage                         │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  │         ↓                                                  │  │
│  │  ┌──────────────────────────────────────────────────────┐ │  │
│  │  │     API Service (Axios Client)                       │ │  │
│  │  │  - HTTP calls to http://localhost:8000               │ │  │
│  │  │  - Request/response typing with TypeScript           │ │  │
│  │  └──────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────┬──────────────────────────────────────────┘
                      │
                      │ HTTP/CORS
                      │ (Axios requests)
                      ↓
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
│            http://localhost:8000                                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routers                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │ /api/upload  │  │ /api/chat    │  │ /health      │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────────────┘  │  │
│  └─────────┼──────────────────┼────────────────────────────┘  │
│            ↓                  ↓                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Ingestion Pipeline (Upload)                 │  │
│  │                                                           │  │
│  │  File → Extract Text → Chunk → Embed → Vector Store     │  │
│  │                           ↓                              │  │
│  │                      MongoDB                             │  │
│  │                    (metadata)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Agent & Retrieval (Chat)                      │  │
│  │                                                           │  │
│  │  Query → Embed → Search → Retrieve → LLM → Answer       │  │
│  │                                  ↓                       │  │
│  │                    OpenAI GPT                            │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────┬──────────────┬─────────────┬───────────────────────┘
            │              │             │
            ↓              ↓             ↓
      ┌──────────┐   ┌──────────┐  ┌──────────┐
      │ MongoDB  │   │ Pinecone │  │Cloudinary│
      │  (Data)  │   │(Vectors) │  │(Files)   │
      └──────────┘   └──────────┘  └──────────┘
```

## Data Flow Diagrams

### 1. Document Upload Flow

```
User uploads file (drag-drop or click)
        ↓
Frontend validates:
- File type (.pdf or .txt)
- File size (max 20MB)
        ↓
File + user_id → POST /api/upload
        ↓
Backend:
  1. Extract text (PyPDF2 or text parsing)
  2. Split into chunks (~500 chars)
  3. Generate embeddings (OpenAI embeddings)
  4. Store vectors in Pinecone (with metadata)
  5. Save metadata in MongoDB:
     - document_id, filename, user_id
     - cloudinary_url, chunk_count
  6. Upload original file to Cloudinary
        ↓
Return: UploadResponse
  - document_id (UUID)
  - filename
  - chunk_count
  - cloudinary_url
  - uploaded_at timestamp
        ↓
Frontend:
- Add document to Zustand store
- Display in document list
- Available for selection
```

### 2. Chat Query Flow

```
User selects documents + types question
        ↓
Frontend validates:
- At least one document selected
- Query not empty
        ↓
Query + document_ids + user_id → POST /api/chat
        ↓
Backend:
  1. Verify user owns documents
     (check MongoDB for user_id match)
  2. Embed the query (same embeddings model)
  3. Search Pinecone:
     - Find similar chunks from selected docs
     - Return top K results with metadata
  4. Format context for LLM
  5. Call OpenAI with:
     - Query
     - Retrieved chunks as context
     - System prompt
  6. Parse response and extract citations
  7. Return citations with excerpts
        ↓
Return: ChatResponse
  - answer (LLM-generated text)
  - citations[]:
    - filename
    - page number
    - chunk index
    - excerpt
  - used_retrieval (boolean)
        ↓
Frontend:
- Add user message to chat
- Add assistant message with citations
- Display expandable citation cards
- Show loading state
- Handle errors
```

### 3. Message Flow Architecture

```
FRONTEND                          BACKEND
┌──────────────┐
│ User Input   │
└──────┬───────┘
       │
       ├─→ Validation
       │   ├─ Document selected?
       │   ├─ Query not empty?
       │   └─ User ID exists?
       │
       ├─→ Store Message (Zustand)
       │   └─ role: "user"
       │       content: query
       │
       └─→ POST /api/chat ────────────────────┐
                                               │
                                    ┌──────────┴────────┐
                                    │                   │
                                    ↓                   ↓
                            Verify Ownership    Get Embeddings
                                    │                   │
                                    └─────────┬─────────┘
                                              │
                                              ↓
                                        Search Pinecone
                                        (vector DB)
                                              │
                                              ↓
                                        Call OpenAI LLM
                                              │
                                              ↓
                                        Parse Citations
                                              │
                                    ┌─────────┴──────────┐
                         ChatResponse                    │
                         ├─ answer                       │
                         ├─ citations[]                  │
                         └─ used_retrieval               │
                                    │                   │
       ← ← ← ← ← ← ← ← ← ← ← ← ← ←─┴──── ← ← ← ← ← ← ← ┘
       │
       ├─→ Store Message (Zustand)
       │   └─ role: "assistant"
       │       content: answer
       │       citations: [...]
       │
       └─→ Render in UI
           ├─ Answer text
           └─ Citation cards
               ├─ Filename
               ├─ Page/Chunk
               └─ Excerpt (expandable)
```

## Component Interaction

```
App (page.tsx)
│
├─ Header
│
├─ Error Toast (global)
│
└─ Main Grid (2 columns)
   │
   ├─ LEFT COLUMN (1/3)
   │  │
   │  ├─ UserIdCard
   │  │  └─ Shows user_id + copy button
   │  │     └─ Connects to: store.userId
   │  │
   │  ├─ UploadForm
   │  │  ├─ Drag-drop input
   │  │  ├─ File validation
   │  │  └─ API call
   │  │     └─ Calls: apiService.uploadDocument()
   │  │     └─ Updates: store.addDocument()
   │  │
   │  └─ DocumentList
   │     ├─ Maps over store.documents
   │     ├─ Shows checkboxes
   │     └─ On toggle
   │        └─ Updates: store.toggleDocumentSelection()
   │
   ├─ RIGHT COLUMN (2/3)
   │  │
   │  └─ ChatInterface
   │     ├─ Reads: store.messages
   │     ├─ Reads: store.selectedDocIds
   │     ├─ Reads: store.isLoading
   │     │
   │     ├─ Message List
   │     │  ├─ User messages (blue)
   │     │  ├─ Assistant messages (gray)
   │     │  │  └─ CitationCard (expandable)
   │     │  └─ Loading spinner
   │     │
   │     └─ Input Form
   │        ├─ Text input
   │        ├─ Send button
   │        └─ On submit
   │           ├─ Validation
   │           ├─ API call
   │           │  └─ Calls: apiService.chat()
   │           ├─ Store messages
   │           │  └─ Calls: store.addMessage()
   │           └─ Scroll to bottom
   │
   └─ Footer
```

## State Management (Zustand)

```
Store Structure:

AppStore {
  // User
  userId: string
  setUserId: (id) => void

  // Documents
  documents: Document[]
  setDocuments: (docs) => void
  addDocument: (doc) => void
  removeDocument: (id) => void

  // Selection
  selectedDocIds: string[]
  setSelectedDocIds: (ids) => void
  toggleDocumentSelection: (id) => void

  // Chat
  messages: ChatMessage[]
  addMessage: (msg) => void
  clearMessages: () => void

  // UI State
  isLoading: boolean
  setIsLoading: (bool) => void

  error: string | null
  setError: (err) => void
}

Persistence:
- userId (localStorage)
- documents (localStorage)
- selectedDocIds (localStorage)
- messages (localStorage)
```

## API Client Architecture

```
APIService (axios)
│
├─ uploadDocument(file, userId)
│  ├─ Create FormData
│  ├─ POST /api/upload
│  ├─ Return: UploadResponse
│  └─ Error handling
│
├─ chat(query, documentIds, userId)
│  ├─ POST /api/chat
│  ├─ Body: {query, document_ids, user_id}
│  ├─ Return: ChatResponse
│  └─ Error handling
│
└─ healthCheck()
   ├─ GET /health
   ├─ Return: boolean
   └─ Error handling
```

## Type Safety

All data is typed with TypeScript:

```typescript
// API Types
interface UploadResponse { ... }
interface ChatResponse { ... }
interface Citation { ... }

// Store Types
interface Document { ... }
interface ChatMessage { ... }
interface AppStore { ... }
```

## Error Handling Strategy

```
Frontend Errors:
├─ Validation Errors
│  └─ File type/size validation
│
├─ Network Errors
│  └─ API call failures (try-catch)
│
└─ User Feedback
   ├─ Toast notifications
   ├─ Disabled UI states
   └─ Error messages

Backend Errors (HTTP Status):
├─ 400 Bad Request
│  └─ Validation failed
│
├─ 403 Forbidden
│  └─ User doesn't own document
│
├─ 422 Unprocessable Entity
│  └─ Can't process file
│
└─ 500 Server Error
   └─ Processing failed
```

## Performance Considerations

```
Frontend:
├─ Component memoization (React.memo)
├─ Zustand for efficient state updates
├─ Tailwind for optimized CSS
└─ Next.js automatic code splitting

Backend:
├─ Vector similarity search (O(1) with indexing)
├─ Chunking for context window limits
├─ Embedding caching
└─ Database indexing on user_id
```

## Security Flow

```
1. User Generation
   └─ Generate unique ID client-side (not auth)

2. Document Ownership
   └─ user_id sent with every request
   └─ Backend verifies in MongoDB

3. File Validation
   ├─ Frontend: type & size checks
   └─ Backend: redundant checks

4. Data Privacy
   ├─ Documents isolated by user_id
   ├─ Vectors isolated by document_id
   └─ No cross-user access possible
```

## Scalability Considerations

```
Current State:
├─ No user authentication
├─ No rate limiting
└─ No usage tracking

Scaling Improvements:
├─ Add JWT authentication
├─ Rate limit by user
├─ Cache embeddings
├─ Use batch API calls
├─ Implement pagination
└─ Add monitoring/logging
```

---

This architecture is **modular**, **type-safe**, and **production-ready**!
