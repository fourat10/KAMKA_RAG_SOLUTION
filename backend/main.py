from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env before anything else so all os.getenv() calls work
load_dotenv()

from api.upload import router as upload_router

app = FastAPI(title="Kamka Document Assistant API")

# Allow the Next.js frontend (localhost:3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}