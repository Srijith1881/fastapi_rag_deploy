from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
import shutil
import uuid
import logging

from rag import build_rag_chain, load_existing_vectorstore, add_to_vectorstore, ensure_env_ready
from pdf import load_pdf

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories for uploads & vector store
UP_DIR = "uploads"
VECTOR_DIR = "vectorstore"
os.makedirs(UP_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)

# Global retriever and RAG chain
rag_chain = None
retriever = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load existing vector store on app start, then clean up on shutdown."""
    global retriever, rag_chain
    try:
        ensure_env_ready()
        retriever = load_existing_vectorstore()
        if retriever:
            rag_chain = build_rag_chain(retriever)
        logger.info("✅ Vectorstore loaded successfully at startup")
    except Exception as e:
        logger.error(f"⚠️ Failed to initialize vectorstore: {e}")
        retriever = None
        rag_chain = None
    yield
    # (No teardown needed)


app = FastAPI(lifespan=lifespan)

# Enable CORS for frontend connection (adjust in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: replace with frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryModel(BaseModel):
    query: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and index a PDF file."""
    global retriever, rag_chain
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="⚠️ Only PDF files are allowed")

        file_id = str(uuid.uuid4())
        file_path = os.path.join(UP_DIR, f"{file_id}.pdf")

        # Save uploaded file
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"❌ Failed to save file: {str(e)}")

        # Process and index PDF
        docs = load_pdf(file_path)
        retriever = add_to_vectorstore(docs)
        rag_chain = build_rag_chain(retriever)

        return {"message": f"✅ File '{file.filename}' uploaded and indexed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"❌ Error uploading file: {str(e)}")


@app.post("/query")
async def query_api(query_data: QueryModel):
    """Answer questions using the RAG chain."""
    global rag_chain
    if rag_chain is None:
        raise HTTPException(status_code=400, detail="⚠️ No PDF indexed yet")

    question = query_data.query.strip()
    if not question:
        raise HTTPException(status_code=400, detail="⚠️ Question is required")

    try:
        reply = rag_chain.invoke({"question": question})
        return {"reply": reply}
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
