import os
import logging
from dotenv import load_dotenv
from operator import itemgetter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Reduce noisy logs and telemetry from dependent libraries
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("langchain").setLevel(logging.WARNING)

# Accept either GOOGLE_API_KEY or legacy API var
def ensure_env_ready():
    try:
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("API")
        if key and not os.getenv("GOOGLE_API_KEY"):
            os.environ["GOOGLE_API_KEY"] = key
        if not os.getenv("GOOGLE_API_KEY"):
            raise RuntimeError("Missing Google Gemini API key. Set GOOGLE_API_KEY (or API) in your .env")
        logger.info("✅ Google API key loaded successfully")
    except Exception as e:
        logger.error(f"❌ Environment setup error: {e}")
        raise


# Embeddings
try:
    embedding = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": "cpu"},
    )
except Exception as e:
    logger.error(f"❌ Failed to load embeddings: {e}")
    raise

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use the provided context to answer the question. If the answer is not in the context, say you don't know. Be concise."),
    ("human", "Context:\n{context}\n\nQuestion: {question}")
])



# LLM
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.3, top_p=0.9)
except Exception as e:
    logger.error(f"❌ Failed to initialize LLM: {e}")
    raise

parser = StrOutputParser()
VECTOR_DIR = "vectorstore"
COLLECTION = "rag_docs"


def load_existing_vectorstore():
    """Load persistent vectorstore if exists"""
    try:
        if os.path.exists(VECTOR_DIR) and os.listdir(VECTOR_DIR):
            vs = Chroma(
                persist_directory=VECTOR_DIR,
                embedding_function=embedding,
                collection_name=COLLECTION,
            )
            logger.info("✅ Vectorstore loaded successfully")
            return vs.as_retriever(search_kwargs={"k": 3})
        return None
    except Exception as e:
        logger.error(f"❌ Failed to load vectorstore: {e}")
        return None


def add_to_vectorstore(docs):
    """Add new docs to persistent Chroma vectorstore"""
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(docs)

        if os.path.exists(VECTOR_DIR) and os.listdir(VECTOR_DIR):
            vs = Chroma(
                persist_directory=VECTOR_DIR,
                embedding_function=embedding,
                collection_name=COLLECTION,
            )
            vs.add_documents(docs)
        else:
            vs = Chroma.from_documents(
                docs,
                embedding,
                persist_directory=VECTOR_DIR,
                collection_name=COLLECTION,
            )

        # ⚠️ No need for vs.persist() → handled automatically
        logger.info("✅ Documents added to vectorstore successfully")
        return vs.as_retriever(search_kwargs={"k": 3})
    except Exception as e:
        logger.error(f"❌ Error adding documents to vectorstore: {e}")
        raise


def indexing(docs):
    """(Not used now) Create new in-memory retriever"""
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = splitter.split_documents(docs)
        vectorstore = Chroma.from_documents(docs, embedding, collection_name=COLLECTION)
        return vectorstore.as_retriever(search_kwargs={"k": 4})
    except Exception as e:
        logger.error(f"❌ Error creating in-memory retriever: {e}")
        raise


def build_rag_chain(retriever):
    try:
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        chain = (
            {
                "context": itemgetter("question") | retriever | format_docs,
                "question": itemgetter("question"),
            }
            | prompt
            | llm
            | parser
        )
        logger.info("✅ RAG chain built successfully")
        return chain
    except Exception as e:
        logger.error(f"❌ Failed to build RAG chain: {e}")
        raise
