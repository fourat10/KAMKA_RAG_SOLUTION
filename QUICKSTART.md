# Getting Started - Quick Reference

## 🚀 30-Second Setup

### Terminal 1: Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Edit .env with your API keys
python main.py
```

### Terminal 2: Frontend

```bash
cd frontend
npm install
npm run dev
```

### Open Browser

```
http://localhost:3000
```

## ✨ What You Can Do

1. **Upload Document** - PDF or TXT (max 20MB)
2. **Select Document** - Checkbox next to filename
3. **Ask Question** - "What is this document about?"
4. **Get Answer** - With citations and source excerpts
5. **Copy User ID** - Share documents with same ID

## 📝 Required API Keys

- OpenAI (gpt-3.5-turbo or gpt-4)
- Pinecone (vector database)
- MongoDB (document storage)
- Cloudinary (file storage)

Get them free or cheap at:

- openai.com
- pinecone.io (free tier available)
- mongodb.com (free tier available)
- cloudinary.com (free tier available)

## 🔍 Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Upload file
curl -X POST http://localhost:8000/api/upload \
  -F "file=@document.pdf" \
  -F "user_id=user_test123"

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this about?",
    "document_ids": ["doc-id-here"],
    "user_id": "user_test123"
  }'
```

## 📂 Important Files

**Frontend:**

- `app/page.tsx` - Main UI
- `lib/api.ts` - API communication
- `lib/store.ts` - State management

**Backend:**

- `main.py` - Server startup
- `api/upload.py` - Upload endpoint
- `api/chat.py` - Chat endpoint

## 🛠️ Common Commands

| Command                           | What it does                  |
| --------------------------------- | ----------------------------- |
| `npm run dev`                     | Start frontend dev server     |
| `npm run build`                   | Build frontend for production |
| `python main.py`                  | Start backend server          |
| `npm install`                     | Install frontend packages     |
| `pip install -r requirements.txt` | Install backend packages      |

## 🔗 URLs

| Service      | URL                          |
| ------------ | ---------------------------- |
| Frontend     | http://localhost:3000        |
| Backend      | http://localhost:8000        |
| API Docs     | http://localhost:8000/docs   |
| Health Check | http://localhost:8000/health |

## 🎨 Customization Tips

**Change UI Colors:**
Edit `frontend/tailwind.config.ts`

**Change API URL:**
Edit `frontend/.env.local`

**Change Model:**
Edit backend and update OpenAI model in agent code

**Add More Features:**

1. Add component in `frontend/components/`
2. Add API in `backend/api/`
3. Connect them together

## ❓ Still Having Issues?

1. Check [SETUP.md](./SETUP.md) for detailed steps
2. Check [README.md](./README.md) for full documentation
3. Verify backend is running: `curl http://localhost:8000/health`
4. Check browser console for errors (F12)
5. Check terminal output for backend errors

## 🎯 Next Steps

After setup works:

1. Try uploading different file types
2. Test with multiple documents
3. Customize the UI colors/layout
4. Deploy to production (see [DEPLOYMENT.md](./DEPLOYMENT.md))
5. Add user authentication

## 💡 Pro Tips

- Drag & drop files to upload faster
- Click citations to expand and see context
- Copy your User ID to share documents
- Chat works better with structured documents
- PDFs with tables work great!

---

Ready? Let's go! 🚀
