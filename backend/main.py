import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from api.upload import router as upload_router
from api.chat import router as chat_router
from api.stream import router as stream_router
from api.debug import router as debug_router

app = FastAPI(title="Kamka Document Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(stream_router, prefix="/api")
app.include_router(debug_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}