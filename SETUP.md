# Setup Guide - Kamka Document Assistant

## Step-by-Step Installation

### Step 1: Prerequisites

Make sure you have installed:

- **Node.js 18+** - [Download](https://nodejs.org/)
- **Python 3.9+** - [Download](https://www.python.org/)
- **Git** (optional)

Verify installations:

```bash
node --version
npm --version
python --version
```

### Step 2: Configure Backend Environment

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Copy the example env file:

   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your API keys:

   ```env
   # OpenAI API Key
   OPENAI_API_KEY=sk-your-key-here

   # Pinecone Vector Database
   PINECONE_API_KEY=your-key-here
   PINECONE_INDEX_NAME=kamka

   # Cloudinary Cloud Storage
   CLOUDINARY_CLOUD_NAME=your-cloud-name
   CLOUDINARY_API_KEY=your-key-here
   CLOUDINARY_API_SECRET=your-secret-here

   # MongoDB Database
   MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/dbname
   ```

   **Where to get these keys:**
   - **OpenAI**: https://platform.openai.com/api-keys
   - **Pinecone**: https://app.pinecone.io/
   - **Cloudinary**: https://cloudinary.com/console/
   - **MongoDB**: https://www.mongodb.com/cloud/atlas

### Step 3: Set Up Backend

1. Create Python virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate virtual environment:
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:

   ```bash
   python main.py
   ```

   You should see:

   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   ```

   Test it's working:

   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"ok"}
   ```

### Step 4: Set Up Frontend

Open a **new terminal** (keep backend running):

1. Navigate to frontend:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Frontend is pre-configured to use `http://localhost:8000` for the API. If your backend runs elsewhere, update `.env.local`:

   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

4. Start the development server:

   ```bash
   npm run dev
   ```

   You should see:

   ```
   ▲ Next.js 14.0.0
   - Local:        http://localhost:3000
   ```

### Step 5: Access the Application

Open your browser and go to:

```
http://localhost:3000
```

You should see the Kamka interface with:

- ✅ User ID displayed (generated automatically)
- ✅ Upload form ready for PDF/TXT files
- ✅ Empty document list
- ✅ Empty chat interface

## First Test

1. **Get your User ID**: Copy the ID shown on the page (starts with `user_`)

2. **Upload a Document**:
   - Create a simple text file or use a PDF
   - Drag it to the upload area or click to select
   - Wait for "uploaded successfully"

3. **Start Chatting**:
   - Check the checkbox next to your document
   - Type a question in the chat box
   - Send the message
   - AI will respond with citations

## Common Issues & Fixes

### "Failed to upload file"

- Check that your file is PDF or TXT
- Ensure file size is under 20MB
- Verify backend is running (`http://localhost:8000/health`)

### "Chat button is disabled"

- Select at least one document
- Ensure your message isn't empty
- Wait for previous response to finish

### "Connection refused" / API errors

- Verify backend is running on port 8000
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Restart both servers if needed

### Python package errors

- Delete `.venv` folder and recreate:
  ```bash
  rm -rf .venv
  python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

### Node module errors

- Delete `node_modules` and reinstall:
  ```bash
  rm -rf node_modules
  npm install
  ```

## Stopping Servers

To stop either server:

- **Backend/Frontend**: Press `Ctrl + C` in the terminal

To deactivate Python environment:

```bash
deactivate
```

## Next Steps

### Development

- Both servers support hot reload
- Edit code and changes appear automatically
- Check browser console for frontend errors
- Check terminal for backend errors

### Customization

- **Styling**: Edit `frontend/app/globals.css` or Tailwind classes
- **API Client**: Modify `frontend/lib/api.ts`
- **Backend Logic**: Edit `backend/api/chat.py` or `backend/api/upload.py`

### Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for production setup.

## Need Help?

1. Check the main [README.md](./README.md) for full documentation
2. Backend docs: [backend/README.md](./backend/README.md)
3. Frontend docs: [frontend/README.md](./frontend/README.md)
4. Check API endpoints in main README under "API Endpoints"

## Summary

```
✅ Backend: http://localhost:8000
✅ Frontend: http://localhost:3000
✅ API: http://localhost:8000/api/upload, /api/chat
✅ Ready to chat with your documents!
```

Happy chatting! 🚀
