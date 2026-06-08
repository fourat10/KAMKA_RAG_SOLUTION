# Kamka - Document Assistant

A full-stack AI document assistant that lets users upload documents and chat with an AI to find answers with citations. Built with **FastAPI** (backend) and **Next.js** (frontend).

## Features

### 🎯 Core Functionality

- **File Upload**: Support for PDF and TXT documents (up to 20MB)
- **Document Management**: Upload, organize, and manage your documents
- **AI Chat**: Ask questions about your documents powered by an LLM
- **Citations**: Get sources and excerpts from your documents
- **User Sessions**: Unique user ID ensures document privacy

### 🎨 Frontend

- **Modern UI**: Clean, intentional design with Tailwind CSS
- **Responsive Layout**: Works on desktop and tablets
- **Loading States**: Smooth feedback during operations
- **Error Handling**: Clear error messages and recovery
- **TypeScript**: Type-safe React components

### ⚡ Backend

- **Document Processing**: Extracts text from PDFs and TXT files
- **Chunking**: Intelligent document chunking for context
- **Embeddings**: Vector embeddings for semantic search
- **Vector Storage**: Pinecone integration for similarity search
- **Cloud Storage**: Cloudinary for file hosting
- **LLM Integration**: Agent-based query system with tool calling

## Project Structure

```
kamka/
├── backend/                 # FastAPI backend
│   ├── api/                # API routes
│   │   ├── upload.py       # File upload endpoint
│   │   ├── chat.py         # Chat endpoint
│   │   └── debug.py        # Debug endpoints
│   ├── agent/              # AI agent and tools
│   ├── ingestion/          # Document processing
│   ├── models/             # Pydantic models
│   ├── services/           # External service clients
│   ├── main.py             # FastAPI app
│   ├── requirements.txt    # Python dependencies
│   └── README.md           # Backend docs
│
└── frontend/               # Next.js frontend
    ├── app/                # Next.js App Router
    │   ├── layout.tsx      # Root layout
    │   ├── page.tsx        # Main page
    │   └── globals.css     # Global styles
    ├── components/         # React components
    │   ├── UploadForm.tsx
    │   ├── DocumentList.tsx
    │   ├── ChatInterface.tsx
    │   ├── CitationCard.tsx
    │   └── UserIdCard.tsx
    ├── lib/                # Utilities
    │   ├── api.ts          # API client
    │   ├── store.ts        # Zustand state management
    │   └── utils.ts        # Helper functions
    ├── public/             # Static assets
    ├── package.json
    └── README.md           # Frontend docs
```

## Quick Start

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.9+ (for backend)
- Environment variables set up (see below)

### Backend Setup

1. **Navigate to backend directory**

   ```bash
   cd backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # - OPENAI_API_KEY
   # - PINECONE_API_KEY
   # - CLOUDINARY_API_KEY
   # - MONGODB_URI
   ```

5. **Run the backend**
   ```bash
   python main.py
   ```
   The backend will start on `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**

   ```bash
   cd frontend
   ```

2. **Install dependencies**

   ```bash
   npm install
   ```

3. **Create environment file**

   ```bash
   cp .env.example .env.local
   # Default is http://localhost:8000, adjust if backend runs elsewhere
   ```

4. **Run development server**
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser

## How It Works

### 1. User Session

- Frontend generates a unique `user_id` on first visit
- Stored locally, persists across page reloads
- All documents are tagged with this ID for privacy

### 2. Document Upload

1. User selects a PDF or TXT file
2. Frontend sends file + user_id to `/api/upload`
3. Backend:
   - Extracts text from document
   - Chunks text into manageable pieces
   - Generates embeddings for chunks
   - Stores vectors in Pinecone
   - Saves document metadata in MongoDB
   - Returns document_id to frontend
4. Frontend displays document in list

### 3. Chat with Documents

1. User selects documents and types a question
2. Frontend sends to `/api/chat` with query + document_ids + user_id
3. Backend:
   - Verifies user owns the documents
   - Injects document IDs into query context
   - Runs agent with query
   - Agent retrieves relevant chunks from Pinecone
   - LLM generates answer with citations
   - Returns citations with document excerpts
4. Frontend displays answer with clickable citations

### 4. Citation System

- Each citation includes:
  - Document filename
  - Page number (if available)
  - Chunk index
  - Excerpt of relevant text
- Users can expand/collapse citations to see context

## API Endpoints

### Health Check

```
GET /health
```

### Upload Document

```
POST /api/upload
Content-Type: multipart/form-data

Parameters:
- file: File (PDF or TXT, max 20MB)
- user_id: string

Response:
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "chunk_count": 42,
  "cloudinary_url": "https://...",
  "uploaded_at": "2024-01-01T00:00:00Z"
}
```

### Chat with Documents

```
POST /api/chat
Content-Type: application/json

Request:
{
  "query": "What does the document say about X?",
  "document_ids": ["doc-uuid-1", "doc-uuid-2"],
  "user_id": "user_xxx"
}

Response:
{
  "answer": "The document mentions...",
  "citations": [
    {
      "reference": "doc-uuid-1",
      "filename": "document.pdf",
      "page": 5,
      "chunk_index": 12,
      "excerpt": "..."
    }
  ],
  "used_retrieval": true
}
```

## Environment Variables

### Backend (.env)

```
# LLM
OPENAI_API_KEY=sk-...

# Vector Database
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=kamka

# Cloud Storage
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...

# Database
MONGODB_URI=mongodb+srv://...

# Offline Models
TRANSFORMERS_OFFLINE=1
HF_DATASETS_OFFLINE=1
```

### Frontend (.env.local)

```
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Technology Stack

### Backend

- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation
- **OpenAI** - LLM for answers
- **Pinecone** - Vector database for embeddings
- **MongoDB** - Document storage
- **Cloudinary** - Cloud file storage
- **PyPDF2/pdfplumber** - PDF processing

### Frontend

- **Next.js 14** - React framework with App Router
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Axios** - HTTP client

## Development

### Running Both Services

```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Building for Production

**Backend:**

```bash
# Using gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

**Frontend:**

```bash
npm run build
npm start
```

## Error Handling

### Common Issues

**CORS Errors**

- Ensure backend allows frontend origin in CORS middleware
- Default: localhost:3000

**File Upload Errors**

- Maximum file size: 20MB
- Supported formats: .pdf, .txt
- File must have extractable text

**Chat Not Working**

- Ensure documents are selected
- Check that documents belong to current user
- Verify API keys are set

## Security Considerations

- ✅ User document ownership verified on backend
- ✅ Unique user IDs prevent cross-user access
- ✅ Files stored on Cloudinary with secure URLs
- ✅ Vector data isolated by document_id
- ✅ Environment variables not exposed to frontend

## Future Enhancements

- [ ] User authentication
- [ ] Document sharing
- [ ] Conversation history
- [ ] Advanced search filters
- [ ] Batch document upload
- [ ] Export chat results
- [ ] Document annotations

## License

MIT

## Support

For issues or questions:

1. Check the backend [README.md](./backend/README.md)
2. Check the frontend [README.md](./frontend/README.md)
3. Review API documentation above
