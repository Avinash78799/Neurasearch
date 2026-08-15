"""
FastAPI Server — Endpoints for document ingestion, query execution (SSE),
evaluation, system settings, document insights, conversation memory, and health checks.
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any, List, Optional
from pydantic import BaseModel

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, status, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from config import settings
from graph.graph import crag_graph
from rag.ingestor import ingest_bytes
from rag.vectorstore import list_sources, delete_by_source, get_documents_by_source
from rag.bm25_index import load_index, rebuild_index
from eval.ragas_eval import run_ragas_eval
from database import db
from research.engine import run_deep_research, ResearchPlanner
from workspace_service import WorkspaceContext, WorkspaceService
from auth import verify_password, create_access_token, get_current_user

# Configure structured logging
from core.logging import setup_logging
import os
setup_logging(log_format=os.environ.get("LOG_FORMAT", "text"))
logger = logging.getLogger("neurasearch.api")

app = FastAPI(title="NeuraSearch", version="2.1.0")

# ── APIRouter for version v1 ─────────────────────────────────────────
v1_router = APIRouter()

# ── Rate Limiting ────────────────────────────────────────────────────
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
class WorkspaceCreateRequest(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

def get_workspace_context(request: Request) -> WorkspaceContext:
    workspace_id = request.headers.get("X-Workspace-ID")
    if not workspace_id:
        workspace_id = settings.default_workspace_id
    username = getattr(request.state, "username", None)
    return WorkspaceContext(workspace_id=workspace_id, username=username)


# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handlers ────────────────────────────────────────
from core.exceptions import (
    NeuraSearchError, WorkspaceError, RetrievalError, ResearchError,
    ComputationError, AuthenticationError, IngestionError, KnowledgeError, KnowledgeConflictError
)

@app.exception_handler(NeuraSearchError)
async def neurasearch_error_handler(request: Request, exc: NeuraSearchError):
    status_map = {
        WorkspaceError: 400,
        RetrievalError: 502,
        ResearchError: 500,
        ComputationError: 422,
        AuthenticationError: 401,
        IngestionError: 400,
        KnowledgeError: 400,
        KnowledgeConflictError: 409,
    }
    status_code = status_map.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={"error": exc.code, "detail": exc.message}
    )

@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    # Exclude public paths
    path = request.url.path
    if path in ["/token", "/health", "/"] or path.startswith("/docs") or path.startswith("/openapi.json"):
        return await call_next(request)
        
    # OPTIONS requests (preflight CORS) should skip auth
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Check authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Not authenticated. Missing or invalid Authorization header."}
        )
    
    # Validate token
    token = auth_header.split(" ")[1]
    from auth import JWT_SECRET_KEY, JWT_ALGORITHM
    import jwt
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise jwt.PyJWTError()
        request.state.username = username
    except jwt.PyJWTError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Could not validate credentials."}
        )
        
    response = await call_next(request)
    return response

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await asyncio.to_thread(db.get_user, form_data.username)
    if not user or not await asyncio.to_thread(verify_password, form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@v1_router.get("/auth/me")
async def get_me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}

# In-memory storage for latest RAGAS evaluation results
latest_eval_results: dict = {
    "faithfulness": None,
    "answer_relevancy": None,
    "context_recall": None,
    "context_precision": None,
    "error": "No evaluation has been run yet",
}


# Background task to generate document insights
async def generate_insights_task(source: str, workspace_id: str):
    """Reconstruct document text and generate summary/topics/entities using LLM."""
    try:
        from insights.analyzer import generate_insights
        
        logger.info("Starting background insights generation for: %s", source)
        chunks = get_documents_by_source(source, context=workspace_id)
        if not chunks:
            logger.warning("No chunks found in vectorstore for %s. Skipping insights.", source)
            return

        # Reconstruct full text in correct order
        def sort_key(doc):
            meta = doc.metadata or {}
            return (meta.get("page_number", 1), meta.get("chunk_index", 0))

        sorted_chunks = sorted(chunks, key=sort_key)
        full_text = "\n".join([c.page_content for c in sorted_chunks])

        # Run analyzer
        insights = await generate_insights(full_text)

        # Save to SQLite DB
        db.save_insights(
            doc_id=str(uuid.uuid4()),
            source=source,
            summary=insights["summary"],
            topics=insights["topics"],
            entities=insights["entities"],
            word_count=insights["word_count"],
            chunk_count=insights["chunk_count"],
            reading_time=insights["reading_time"],
            context=workspace_id
        )
        logger.info("Successfully generated and saved insights for %s", source)
    except Exception as e:
        logger.error("Error generating insights for %s in background: %s", source, e, exc_info=True)


# Shutdown event
@app.on_event("shutdown")
def shutdown_event():
    """Close the LangGraph checkpointer SQLite context gracefully."""
    logger.info("Stopping NeuraSearch backend server and closing checkpointer...")
    try:
        from graph.graph import checkpointer_context
        checkpointer_context.__exit__(None, None, None)
    except Exception as e:
        logger.error("Error closing checkpointer context: %s", e)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialise the BM25 index and trigger missing insights on start."""
    logger.info("Starting NeuraSearch backend server...")
    
    # Load BM25 index for default workspace
    WorkspaceService.ensure_default_workspace()
    success = load_index(settings.default_workspace_id)
    if not success:
        logger.warning(
            "Could not load BM25 index from pickle. If ChromaDB has data, please trigger a rebuild."
        )

    # Scan for any documents that are in vectorstore but do not have database insights cached
    try:
        sources = list_sources(settings.default_workspace_id)
        for src in sources:
            existing = db.get_insights(src, context=settings.default_workspace_id)
            if not existing:
                logger.info("Missing database insights for source '%s'. Triggering generation task...", src)
                asyncio.create_task(generate_insights_task(src, settings.default_workspace_id))
    except Exception as e:
        logger.error("Failed startup insights scan: %s", e)



@v1_router.get("/workspaces")
async def list_workspaces_route(context: WorkspaceContext = Depends(get_workspace_context)):
    try:
        return {"workspaces": WorkspaceService.list_workspaces()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workspaces: {e}")

@v1_router.post("/workspaces")
async def create_workspace_route(req: WorkspaceCreateRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    try:
        result = WorkspaceService.create_workspace(req.id, req.name, req.description)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workspace: {e}")


@v1_router.post("/workspaces/export/{workspace_id}")
async def export_workspace_route(workspace_id: str):
    """Export workspace knowledge assets to a JSON object."""
    from workspace_transfer_service import WorkspaceTransferService
    import tempfile
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        data = WorkspaceTransferService.export_workspace(workspace_id, tmp_path)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export workspace: {e}")

@v1_router.post("/workspaces/import/{workspace_id}")
async def import_workspace_route(workspace_id: str, file: UploadFile = File(...)):
    """Import workspace knowledge assets from an uploaded JSON archive file."""
    from workspace_transfer_service import WorkspaceTransferService
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)
            
        WorkspaceTransferService.import_workspace(workspace_id, tmp_path)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import workspace: {e}")

@app.get("/")
async def root_endpoint():
    """Welcome root endpoint."""
    return {
        "status": "online",
        "message": "Welcome to NeuraSearch v2 API Server!"
    }


class QueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None



class CompareRequest(BaseModel):
    source_a: str
    source_b: str
    topic: str


class ResearchExecuteRequest(BaseModel):
    session_id: str
    sub_queries: List[str]



class SettingsUpdateRequest(BaseModel):
    pro_mode: Optional[bool] = None
    enable_hallucination_check: Optional[bool] = None
    enable_hyde: Optional[bool] = None
    llm_provider: Optional[str] = None
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    ollama_llm_model: Optional[str] = None


@v1_router.post("/ingest")
async def ingest_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = None, context: WorkspaceContext = Depends(get_workspace_context)):
    """Upload and ingest a PDF or text document, then trigger insights extraction."""
    logger.info("Received ingestion request for: %s", file.filename)
    try:
        # Gating document counts for free tier
        if not settings.pro_mode:
            existing_sources = await asyncio.to_thread(list_sources, context)
            if len(existing_sources) >= settings.max_documents_free and file.filename not in existing_sources:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Free Tier limit reached. Maximum {settings.max_documents_free} documents allowed. Please upgrade to Pro."
                )

        content = await file.read()
        stats = await asyncio.to_thread(ingest_bytes, content, file.filename, context)
        if stats.get("status") != "success":
            raise HTTPException(status_code=400, detail=stats.get("status"))

        # Queue insights generator task
        if background_tasks:
            background_tasks.add_task(generate_insights_task, file.filename, context.workspace_id)
        else:
            asyncio.create_task(generate_insights_task(file.filename, context.workspace_id))

        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to ingest document %s: %s", file.filename, e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@v1_router.post("/query")
async def query_pipeline(request: QueryRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Run the CRAG pipeline and stream execution steps via Server-Sent Events (SSE)."""
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    logger.info("Executing query streaming: '%s' (conversation: %s)", question, request.conversation_id)

    # 1. Check exact-match query cache in SQLite
    try:
        with db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT m_ast.content, m_ast.metadata, c.id as conv_id
                FROM messages m_usr
                JOIN messages m_ast ON m_usr.conversation_id = m_ast.conversation_id
                JOIN conversations c ON m_usr.conversation_id = c.id
                WHERE m_usr.role = 'user' 
                  AND m_usr.content = ? AND m_usr.workspace_id = ? 
                  AND m_ast.role = 'assistant'
                  AND m_ast.created_at > m_usr.created_at
                ORDER BY m_usr.created_at DESC
                LIMIT 1
                """,
                (question, context.workspace_id)
            ).fetchone()
            
            if row:
                logger.info("Cache hit for question: '%s'", question)
                cached_answer = row["content"]
                cached_metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                cached_conv_id = row["conv_id"]
                
                async def cache_event_stream():
                    yield f"data: {json.dumps({'type': 'step', 'data': 'Checking query cache... (Hit)'})}\n\n"
                    await asyncio.sleep(0.05)
                    yield f"data: {json.dumps({'type': 'step', 'data': 'Retrieving cached answer...'})}\n\n"
                    await asyncio.sleep(0.05)
                    
                    result_payload = {
                        "type": "result",
                        "data": {
                            "conversation_id": cached_conv_id,
                            "answer": cached_answer,
                            "sources": cached_metadata.get("citations", []),
                            "retrieval_quality": cached_metadata.get("retrieval_quality", "good"),
                            "hallucination_check": cached_metadata.get("hallucination_check", "grounded"),
                            "steps": cached_metadata.get("steps", ["Query Cache Hit"]),
                            "observability": {
                                "llm_latency_sec": 0.0,
                                "retrieval_latency_sec": 0.0,
                                "total_latency_sec": 0.1,
                                "embedding_time_sec": 0.0,
                                "cache_hit": True
                            }
                        },
                    }
                    yield f"data: {json.dumps(result_payload)}\n\n"
                
                return StreamingResponse(
                    cache_event_stream(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "X-Accel-Buffering": "no",
                    },
                )
    except Exception as e:
        logger.error("Failed query cache lookup: %s", e)

    # 2. Cache Miss: Run CRAG graph pipeline and record latencies
    async def event_generator():
        import time
        total_start = time.time()
        
        node_latencies = {}
        last_node_time = time.time()

        past_messages = []
        if request.conversation_id:
            try:
                past_messages = db.get_messages(request.conversation_id, context=context)
            except Exception as e:
                logger.error("Failed to load past messages: %s", e)

        initial_state = {
            "question": question,
            "workspace_id": context.workspace_id,
            "retry_count": 0,
            "messages": past_messages,
            "steps_taken": [],
        }

        current_state = {
            "question": question,
            "retry_count": 0,
            "messages": past_messages,
            "steps_taken": [],
        }

        try:
            # Stream graph updates node by node
            async for chunk in crag_graph.astream(initial_state, stream_mode="updates"):
                node_end_time = time.time()
                for node_name, node_update in chunk.items():
                    # Calculate duration for this node
                    duration = round(node_end_time - last_node_time, 2)
                    node_latencies[node_name] = duration

                    # Merge update into current_state
                    for k, v in node_update.items():
                        if k in ("steps_taken", "messages"):
                            current_state[k] = current_state[k] + v
                        else:
                            current_state[k] = v

                    # Stream steps_taken from this node
                    if "steps_taken" in node_update:
                        for step in node_update["steps_taken"]:
                            event = {
                                "type": "step",
                                "data": f"{step} (took {duration}s)" if duration > 0.05 else step,
                                "node": node_name,
                                "duration": duration
                            }
                            yield f"data: {json.dumps(event)}\n\n"
                            # Add tiny sleep to smooth UI presentation
                            await asyncio.sleep(0.05)
                
                last_node_time = time.time()

            # Retrieve final values
            generation = current_state.get("generation", "Failed to generate answer")
            sources = current_state.get("sources") or []
            quality = current_state.get("retrieval_quality", "bad")
            hallucination_check = current_state.get("hallucination_check", "grounded")
            steps = current_state.get("steps_taken") or []

            # Compute observability statistics
            total_duration = round(time.time() - total_start, 2)
            retrieval_latency = node_latencies.get("retrieve", 0.0)
            llm_latency = node_latencies.get("generate", 0.0)
            hyde_latency = node_latencies.get("hyde", 0.0) + node_latencies.get("embed_query", 0.0)

            observability_data = {
                "llm_latency_sec": llm_latency,
                "retrieval_latency_sec": retrieval_latency,
                "total_latency_sec": total_duration,
                "embedding_time_sec": hyde_latency,
                "cache_hit": False,
                "node_latencies": node_latencies
            }

            # Save the conversation and messages to DB
            conv_id = request.conversation_id
            try:
                if not conv_id:
                    conv_id = str(uuid.uuid4())
                    title = question[:40] + ("..." if len(question) > 40 else "")
                    db.create_conversation(conv_id, title, context=context)
                
                # Save User message
                db.add_message(
                    msg_id=str(uuid.uuid4()),
                    conv_id=conv_id,
                    role="user",
                    content=question,
                    context=context
                )
                
                # Save Assistant message
                db.add_message(
                    msg_id=str(uuid.uuid4()),
                    conv_id=conv_id,
                    role="assistant",
                    content=generation,
                    context=context,
                    metadata={
                        "citations": sources,
                        "steps": steps,
                        "retrieval_quality": quality,
                        "hallucination_check": hallucination_check,
                        "observability": observability_data
                    }
                )
            except Exception as e:
                logger.error("Failed to save query interaction to database: %s", e)

            # Send final results payload
            result_payload = {
                "type": "result",
                "data": {
                    "conversation_id": conv_id,
                    "answer": generation,
                    "sources": sources,
                    "retrieval_quality": quality,
                    "hallucination_check": hallucination_check,
                    "steps": steps,
                    "observability": observability_data
                },
            }
            yield f"data: {json.dumps(result_payload)}\n\n"

        except Exception as e:
            logger.error("Query pipeline failed: %s", e, exc_info=True)
            error_event = {"type": "step", "data": f"Error running pipeline: {str(e)}"}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@v1_router.get("/documents")
async def list_documents(context: WorkspaceContext = Depends(get_workspace_context)):
    """List all unique source documents currently stored and their insights metadata."""
    try:
        sources = await asyncio.to_thread(list_sources, context)
        result = []
        for src in sources:
            insights = await asyncio.to_thread(db.get_insights, src, context)
            if insights:
                result.append({
                    "source": src,
                    "summary": insights["summary"],
                    "topics": insights["topics"],
                    "entities": insights["entities"],
                    "word_count": insights["word_count"],
                    "chunk_count": insights["chunk_count"],
                    "reading_time": insights["reading_time_min"],
                    "insights_status": "ready"
                })
            else:
                result.append({
                    "source": src,
                    "insights_status": "pending"
                })
        return {"documents": result}
    except Exception as e:
        logger.error("Failed to list documents: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@v1_router.delete("/documents/{source}")
async def delete_document(source: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Delete a document, remove insights cache, and rebuild the BM25 index."""
    logger.info("Received request to delete document: %s", source)
    try:
        # Delete from vector store
        await asyncio.to_thread(delete_by_source, source, context)
        # Delete insights from SQLite
        await asyncio.to_thread(db.delete_insights, source, context)
        # Rebuild BM25 index
        await asyncio.to_thread(rebuild_index, context)
        return {"status": "success", "message": f"Deleted {source}"}
    except Exception as e:
        logger.error("Failed to delete document %s: %s", source, e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Document Insights Endpoints ─────────────────────────────────────
@v1_router.post("/insights/generate/{source}")
async def trigger_insights_generation(source: str, background_tasks: BackgroundTasks, context: WorkspaceContext = Depends(get_workspace_context)):
    """Trigger insights generation manually for a document."""
    background_tasks.add_task(generate_insights_task, source, context.workspace_id)
    return {"status": "success", "message": f"Insights generation triggered for {source}"}


@v1_router.get("/insights/{source}")
async def get_insights_endpoint(source: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Retrieve the cached insights for a document."""
    insights = db.get_insights(source, context=context)
    if not insights:
        raise HTTPException(status_code=404, detail=f"Insights not yet generated for {source}")
    return insights


@v1_router.post("/insights/compare")
async def compare_documents_endpoint(req: CompareRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Compare two documents on a specific topic (Pro feature)."""
    if not settings.pro_mode:
        raise HTTPException(status_code=403, detail="Document comparison is a Pro tier feature.")
    
    from insights.analyzer import compare_documents

    chunks_a = get_documents_by_source(req.source_a, context=context)
    chunks_b = get_documents_by_source(req.source_b, context=context)
    
    if not chunks_a or not chunks_b:
        raise HTTPException(status_code=404, detail="One or both of the comparison documents could not be found.")

    text_a = "\n".join([c.page_content for c in chunks_a])
    text_b = "\n".join([c.page_content for c in chunks_b])

    return await compare_documents(req.source_a, text_a, req.source_b, text_b, req.topic)


# ── Conversation History Endpoints ───────────────────────────────────
@v1_router.get("/conversations")
async def get_conversations_endpoint(context: WorkspaceContext = Depends(get_workspace_context)):
    """List all conversations."""
    try:
        convs = db.list_conversations(context=context)
        # Enforce Free Tier history limit
        if not settings.pro_mode:
            convs = convs[:5]
        return {"conversations": convs}
    except Exception as e:
        logger.error("Failed to fetch conversations: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@v1_router.get("/conversations/{conv_id}/messages")
async def get_conversation_messages_endpoint(conv_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Get all messages in a specific conversation."""
    try:
        messages = db.get_messages(conv_id, context=context)
        return {"messages": messages}
    except Exception as e:
        logger.error("Failed to fetch conversation messages: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@v1_router.delete("/conversations/{conv_id}")
async def delete_conversation_endpoint(conv_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Delete a conversation history."""
    try:
        db.delete_conversation(conv_id, context=context)
        return {"status": "success", "message": f"Conversation {conv_id} deleted."}
    except Exception as e:
        logger.error("Failed to delete conversation: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Deep Research Endpoints ──────────────────────────────────────────
# ── Deep Research Endpoints ──────────────────────────────────────────
@v1_router.post("/research/blueprint")
@limiter.limit(settings.rate_limit_research)
async def create_research_blueprint_endpoint(request: Request, question_request: QueryRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Plan research strategy and generate sub-queries (Research Blueprint)."""
    if not settings.pro_mode:
        raise HTTPException(status_code=403, detail="Deep Research Mode is a Pro tier feature.")
    
    question = question_request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Research question cannot be empty.")
        
    try:
        blueprint = await ResearchPlanner.generate_blueprint(question)
        session_id = str(uuid.uuid4())
        
        # Save session to SQLite
        await asyncio.to_thread(
            db.save_research_session,
            session_id=session_id,
            workspace_id=context.workspace_id,
            status="blueprint",
            original_question=question,
            blueprint=blueprint,
            thread_id=session_id
        )
        
        return {
            "session_id": session_id,
            "question": question,
            "blueprint": blueprint
        }
    except Exception as e:
        logger.error("Failed to generate research blueprint: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@v1_router.post("/research/execute")
@limiter.limit(settings.rate_limit_research)
async def execute_research_endpoint(request: Request, req: ResearchExecuteRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Execute parallel sub-query retrieval and synthesize final research report."""
    if not settings.pro_mode:
        raise HTTPException(status_code=403, detail="Deep Research Mode is a Pro tier feature.")
        
    # Verify session exists
    session = await asyncio.to_thread(db.get_research_session, req.session_id, context)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found or access denied.")
        
    question = session["original_question"]
    sub_queries = req.sub_queries
    
    # Update status to executing
    await asyncio.to_thread(db.update_research_session_status, req.session_id, "executing", context)
    
    async def event_stream():
        try:
            async for event in run_deep_research(question, sub_queries=sub_queries, context=context):
                yield event
            # Update status to completed on success
            await asyncio.to_thread(db.update_research_session_status, req.session_id, "completed", context)
        except Exception as e:
            logger.error("Error running deep research session %s: %s", req.session_id, e)
            await asyncio.to_thread(db.update_research_session_status, req.session_id, "failed", context)
            yield f"data: {json.dumps({'type': 'research_error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@v1_router.post("/research")
@limiter.limit(settings.rate_limit_research)
async def start_research_endpoint(request: Request, question_request: QueryRequest):
    """Execute multi-step deep research and stream reports via SSE (Pro feature)."""
    if not settings.pro_mode:
        raise HTTPException(status_code=403, detail="Deep Research Mode is a Pro tier feature.")
    
    question = question_request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Research question cannot be empty.")

    logger.info("Executing deep research streaming: '%s'", question)

    async def event_stream():
        async for event in run_deep_research(question):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@v1_router.get("/research/reports")
async def get_research_reports_endpoint(context: WorkspaceContext = Depends(get_workspace_context)):
    """List all saved research reports."""
    try:
        reports = db.list_research_reports(context=context)
        return {"reports": reports}
    except Exception as e:
        logger.error("Failed to fetch research reports: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@v1_router.get("/research/reports/{report_id}")
async def get_research_report_endpoint(report_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Fetch detail for a specific research report."""
    report = db.get_research_report(report_id, context=context)
    if not report:
        raise HTTPException(status_code=404, detail="Research report not found.")
    return report


@v1_router.post("/research/reports/{report_id}/pin")
async def pin_research_report_endpoint(report_id: str, payload: dict, context: WorkspaceContext = Depends(get_workspace_context)):
    """Pin or unpin a research report."""
    try:
        is_pinned = payload.get("is_pinned", False)
        db.toggle_pin_report(report_id, is_pinned, context=context)
        return {"status": "success", "message": "Report pin state toggled."}
    except Exception as e:
        logger.error("Failed to pin report: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@v1_router.delete("/research/reports/{report_id}")
async def delete_research_report_endpoint(report_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Delete a research report."""
    try:
        db.delete_research_report(report_id, context=context)
        return {"status": "success", "message": "Report deleted."}
    except Exception as e:
        logger.error("Failed to delete report: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Knowledge Hub Endpoints ──────────────────────────────────────────
from knowledge_service import KnowledgeService
from models.knowledge import CreateKnowledgeItemRequest, UpdateKnowledgeItemRequest, KnowledgeType

@v1_router.post("/knowledge")
async def create_knowledge_item_endpoint(req: CreateKnowledgeItemRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Create a new knowledge item in the active workspace context."""
    return KnowledgeService.create_item(req, context)

@v1_router.get("/knowledge")
async def list_knowledge_items_endpoint(type: Optional[KnowledgeType] = None, status: str = "active", context: WorkspaceContext = Depends(get_workspace_context)):
    """List knowledge items filtered by type/status under workspace context."""
    type_val = type.value if type else None
    return {"items": KnowledgeService.list_items(context, type_val, status)}

@v1_router.get("/knowledge/{id}")
async def get_knowledge_item_endpoint(id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Fetch details of a single knowledge item."""
    return KnowledgeService.get_item(id, context)

@v1_router.put("/knowledge/{id}")
async def update_knowledge_item_endpoint(id: str, req: UpdateKnowledgeItemRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Update item content verifying version match (optimistic lock)."""
    return KnowledgeService.update_item(id, req, context)

@v1_router.patch("/knowledge/{id}/status")
async def update_knowledge_item_status_endpoint(id: str, payload: dict, context: WorkspaceContext = Depends(get_workspace_context)):
    """Archive or soft delete a knowledge item."""
    new_status = payload.get("status", "active")
    if new_status not in ["active", "archived", "deleted"]:
        raise HTTPException(status_code=400, detail="Invalid status value.")
    return KnowledgeService.update_status(id, new_status, context)

@v1_router.patch("/knowledge/{id}/pin")
async def toggle_knowledge_item_pin_endpoint(id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Toggle pinned status for an item."""
    return KnowledgeService.toggle_pin(id, context)


# ── AI Note Generation Endpoints ─────────────────────────────────────
from ai_note_service import AINoteService
from models.ai_notes import GenerateFromChatRequest, GenerateFromReportRequest, GenerateFromEvidenceRequest

@v1_router.post("/knowledge/generate/chat")
async def generate_from_chat_endpoint(req: GenerateFromChatRequest):
    """Generate an AI note draft from a chat question and answer."""
    return await AINoteService.draft_from_chat(req)

@v1_router.post("/knowledge/generate/report")
async def generate_from_report_endpoint(req: GenerateFromReportRequest):
    """Generate an AI note draft from a research report."""
    return await AINoteService.draft_from_report(req)

@v1_router.post("/knowledge/generate/evidence")
async def generate_from_evidence_endpoint(req: GenerateFromEvidenceRequest):
    """Generate an AI note draft from document/evidence context."""
    return await AINoteService.draft_from_evidence(req)


# ── Knowledge Page Endpoints ─────────────────────────────────────────
from knowledge_page_service import KnowledgePageService
from fastapi import Response

class ReferenceRequest(BaseModel):
    item_id: str
    position: int = 0

class ReorderRequest(BaseModel):
    item_ids: List[str]

@v1_router.get("/knowledge/page/{page_id}/references")
async def get_page_references_endpoint(page_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Fetch all referenced notes and insights in order."""
    refs = KnowledgePageService.get_references(page_id, context)
    return {"references": refs}

@v1_router.post("/knowledge/page/{page_id}/references")
async def add_page_reference_endpoint(page_id: str, req: ReferenceRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Add a reference link to a note/insight from a page."""
    KnowledgePageService.add_reference(page_id, req.item_id, req.position, context)
    return {"status": "success", "message": "Reference added."}

@v1_router.delete("/knowledge/page/{page_id}/references/{item_id}")
async def remove_page_reference_endpoint(page_id: str, item_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Remove a reference link from a page."""
    KnowledgePageService.remove_reference(page_id, item_id, context)
    return {"status": "success", "message": "Reference removed."}

@v1_router.put("/knowledge/page/{page_id}/references/reorder")
async def reorder_page_references_endpoint(page_id: str, req: ReorderRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Update positions of all referenced items on the page."""
    KnowledgePageService.reorder_references(page_id, req.item_ids, context)
    return {"status": "success", "message": "Reordering complete."}

@v1_router.post("/knowledge/page/{page_id}/ai-organize")
async def ai_organize_page_endpoint(page_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Get suggested logical order of referenced items using LLM analysis."""
    suggested_ids = await KnowledgePageService.ai_organize_page(page_id, context)
    return {"suggested_order": suggested_ids}

@v1_router.get("/knowledge/page/{page_id}/export")
async def export_page_endpoint(page_id: str, format: str = "markdown", context: WorkspaceContext = Depends(get_workspace_context)):
    """Export page and all its references stitched as Markdown, PDF, or DOCX."""
    page = db.get_knowledge_item(page_id, context)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found.")
    slug = page.get("slug", "export")
    
    if format == "pdf":
        pdf_bytes = KnowledgePageService.export_pdf(page_id, context)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={slug}.pdf"}
        )
    elif format == "docx":
        docx_bytes = KnowledgePageService.export_docx(page_id, context)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={slug}.docx"}
        )
    else: # markdown
        md_text = KnowledgePageService.export_markdown(page_id, context)
        return Response(
            content=md_text,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={slug}.md"}
        )


# ── Collection Endpoints ─────────────────────────────────────────────
from collection_service import CollectionService

class CollectionItemRequest(BaseModel):
    item_id: str
    position: int = 0

class CollectionReorderRequest(BaseModel):
    item_ids: List[str]

@v1_router.get("/knowledge/collection/{collection_id}/items")
async def get_collection_items_endpoint(collection_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Fetch all referenced notes/insights/pages in the collection."""
    items = CollectionService.get_items(collection_id, context)
    return {"items": items}

@v1_router.post("/knowledge/collection/{collection_id}/items")
async def add_collection_item_endpoint(collection_id: str, req: CollectionItemRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Add an item reference to a collection."""
    CollectionService.add_item(collection_id, req.item_id, req.position, context)
    return {"status": "success", "message": "Item added to collection."}

@v1_router.delete("/knowledge/collection/{collection_id}/items/{item_id}")
async def remove_collection_item_endpoint(collection_id: str, item_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Remove an item reference from a collection."""
    CollectionService.remove_item(collection_id, item_id, context)
    return {"status": "success", "message": "Item removed from collection."}

@v1_router.put("/knowledge/collection/{collection_id}/items/reorder")
async def reorder_collection_items_endpoint(collection_id: str, req: CollectionReorderRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Update positions of all referenced items in the collection."""
    CollectionService.reorder_items(collection_id, req.item_ids, context)
    return {"status": "success", "message": "Reordering complete."}


# ── Universal Search Endpoints ────────────────────────────────────────
from knowledge_search_service import KnowledgeSearchService
from models.search import SearchRequest
from models.reading import ReadingProgress, HighlightCreate, SaveNoteRequest, SavePageRequest, DocumentChatRequest

@v1_router.post("/search")
async def quick_search_endpoint(req: SearchRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Perform fast keyword search across knowledge base, reports, and chunks."""
    return await KnowledgeSearchService.quick_search(req, context)

@v1_router.post("/search/deep")
async def deep_search_endpoint(req: SearchRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Perform hybrid vector-BM25 search, FlashRank reranking, and AI synthesis."""
    return await KnowledgeSearchService.deep_search(req, context)

@v1_router.post("/search/research")
async def search_research_endpoint(req: SearchRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Perform deep multi-query research and return the final report."""
    return await KnowledgeSearchService.research_search(req, context)

@v1_router.get("/search/suggestions")
async def search_suggestions_endpoint(query: str = "", context: WorkspaceContext = Depends(get_workspace_context)):
    """Provide real-time autocomplete suggestions under 100ms."""
    suggestions = await KnowledgeSearchService.autocomplete(query, context)
    return {"suggestions": suggestions}


# ── Reading Workspace Endpoints (Added in Module 6) ──────────────────
@v1_router.get("/reading/session/{document}")
async def get_reading_session_endpoint(document: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Load or create reading session context and reconstruct document pages."""
    from reading_workspace_service import ReadingWorkspaceService
    return ReadingWorkspaceService.get_workspace_session(document, context)

@v1_router.post("/reading/progress")
async def save_reading_progress_endpoint(progress: ReadingProgress, context: WorkspaceContext = Depends(get_workspace_context)):
    """Persist page scroll, and zoom positions for a session."""
    from reading_workspace_service import ReadingWorkspaceService
    ReadingWorkspaceService.save_progress(progress.document_id, progress.last_page, progress.scroll_position, progress.zoom_level, context)
    return {"status": "success"}

@v1_router.post("/reading/highlight")
async def create_highlight_endpoint(req: HighlightCreate, context: WorkspaceContext = Depends(get_workspace_context)):
    """Save text highlight passage under current document."""
    from highlight_service import HighlightService
    return HighlightService.create_highlight(
        workspace_id=context.workspace_id,
        document_id=req.document_id,
        page_number=req.page_number,
        highlight_text=req.highlight_text,
        coordinates_json=req.coordinates_json
    )

@v1_router.delete("/reading/highlight/{id}")
async def delete_highlight_endpoint(id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """Delete a highlight snippet."""
    from highlight_service import HighlightService
    success = HighlightService.delete_highlight(context.workspace_id, id)
    if not success:
        raise HTTPException(status_code=404, detail="Highlight not found or access denied")
    return {"status": "success"}

@v1_router.get("/reading/highlights")
async def get_highlights_endpoint(document_id: str, context: WorkspaceContext = Depends(get_workspace_context)):
    """List all highlights of a document."""
    from highlight_service import HighlightService
    return HighlightService.list_highlights(context.workspace_id, document_id)

@v1_router.post("/reading/chat")
async def document_chat_endpoint(req: DocumentChatRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Run document-scoped question answering chat with AI."""
    from reading_workspace_service import ReadingWorkspaceService
    ans = await ReadingWorkspaceService.chat_with_document(req.message, req.document_id, context)
    return {"response": ans}

@v1_router.post("/reading/save-note")
async def save_note_endpoint(req: SaveNoteRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Convert highlight passage to a persistent knowledge note."""
    from highlight_service import HighlightService
    return HighlightService.save_as_note(
        workspace_id=context.workspace_id,
        highlight_text=req.highlight_text,
        document_id=req.document_id,
        title=req.title
    )

@v1_router.post("/reading/save-page")
async def save_page_endpoint(req: SavePageRequest, context: WorkspaceContext = Depends(get_workspace_context)):
    """Append highlight content directly into a page's markdown."""
    from highlight_service import HighlightService
    return HighlightService.save_to_page(
        workspace_id=context.workspace_id,
        highlight_text=req.highlight_text,
        page_id=req.page_id,
        context=context
    )


# ── Settings & Usage Endpoints ───────────────────────────────────────
@v1_router.get("/settings")
async def get_settings_endpoint():
    """Get active configuration parameters and model provider status."""
    return {
        "pro_mode": settings.pro_mode,
        "enable_hallucination_check": settings.enable_hallucination_check,
        "enable_hyde": settings.enable_hyde,
        "llm_temperature": settings.llm_temperature,
        "max_documents_free": settings.max_documents_free,
        "edition": settings.edition,
        "llm_provider": settings.llm_provider,
        "ollama_llm_model": settings.ollama_llm_model,
        "groq_model": settings.groq_model,
        "openai_model": settings.openai_model,
        "has_groq_key": bool(settings.groq_api_key),
        "has_openai_key": bool(settings.openai_api_key),
        "has_deepseek_key": bool(settings.deepseek_api_key),
    }


@v1_router.put("/settings")
async def update_settings_endpoint(req: SettingsUpdateRequest):
    """Update configurable settings and active model provider."""
    if req.pro_mode is not None:
        settings.pro_mode = req.pro_mode
    if req.enable_hallucination_check is not None:
        settings.enable_hallucination_check = req.enable_hallucination_check
    if req.enable_hyde is not None:
        settings.enable_hyde = req.enable_hyde
    if req.llm_provider is not None:
        settings.llm_provider = req.llm_provider.lower().strip()
    if req.groq_api_key is not None:
        settings.groq_api_key = req.groq_api_key.strip() or None
    if req.openai_api_key is not None:
        settings.openai_api_key = req.openai_api_key.strip() or None
    if req.deepseek_api_key is not None:
        settings.deepseek_api_key = req.deepseek_api_key.strip() or None
    if req.ollama_llm_model is not None:
        settings.ollama_llm_model = req.ollama_llm_model.strip()

    # Reset model registry singleton to apply new provider settings
    import core.model_registry
    core.model_registry._llm = None
    
    return {
        "status": "success",
        "settings": {
            "pro_mode": settings.pro_mode,
            "enable_hallucination_check": settings.enable_hallucination_check,
            "enable_hyde": settings.enable_hyde,
            "llm_provider": settings.llm_provider,
            "ollama_llm_model": settings.ollama_llm_model,
            "has_groq_key": bool(settings.groq_api_key),
            "has_openai_key": bool(settings.openai_api_key),
        }
    }


@v1_router.get("/usage")
async def get_usage_endpoint(context: WorkspaceContext = Depends(get_workspace_context)):
    """Return document and conversation usage limits for Free Tier checks."""
    try:
        sources = list_sources(context)
        convs = db.list_conversations(context=context)
        return {
            "pro_mode": settings.pro_mode,
            "document_count": len(sources),
            "max_documents_free": settings.max_documents_free,
        "edition": settings.edition,
            "conversation_count": len(convs),
        }
    except Exception as e:
        logger.error("Failed to fetch usage: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@v1_router.get("/eval/run")
async def run_evaluation():
    """Run RAGAS evaluation using test cases from tests/eval_testset.json."""
    global latest_eval_results

    # Look for eval_testset.json in potential locations
    root_dir = Path(__file__).resolve().parent.parent
    paths_to_check = [
        root_dir / "tests" / "eval_testset.json",
        Path("/app/tests/eval_testset.json"),
        Path("./tests/eval_testset.json"),
    ]
    
    testset_path = None
    for p in paths_to_check:
        if p.exists():
            testset_path = p
            break

    if not testset_path:
        # Create a default testset file if it doesn't exist
        testset_dir = root_dir / "tests"
        testset_dir.mkdir(exist_ok=True)
        testset_path = testset_dir / "eval_testset.json"
        default_testset = [
            {
                "user_input": "What is NeuraSearch?",
                "reference": "NeuraSearch is a local self-correcting AI research assistant that runs 100% locally using Llama 3.3 and LangGraph.",
            },
            {
                "user_input": "How does HyDE improve retrieval?",
                "reference": "HyDE generates a hypothetical ideal answer first, then embeds that answer and uses it for similarity search instead of the raw question.",
            },
        ]
        with open(testset_path, "w") as f:
            json.dump(default_testset, f, indent=2)
        logger.info("Created default test set at: %s", testset_path)

    try:
        with open(testset_path, "r") as f:
            raw_cases = json.load(f)
    except Exception as e:
        logger.error("Failed to load testset: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to load test set: {str(e)}")

    logger.info("Running evaluation on %d test cases...", len(raw_cases))
    processed_cases = []

    # Run the CRAG graph pipeline for each case to collect generation and context
    for tc in raw_cases:
        question = tc.get("user_input")
        reference = tc.get("reference")
        if not question or not reference:
            continue

        try:
            logger.info("Evaluating test question: '%s'", question)
            initial_state = {
                "question": question,
                "retry_count": 0,
                "messages": [],
                "steps_taken": [],
            }
            # Run graph to get response
            final_state = await crag_graph.ainvoke(initial_state)
            
            response = final_state.get("generation", "")
            final_context = final_state.get("final_context") or []
            contexts = [doc.get("content", "") for doc in final_context]

            processed_cases.append({
                "user_input": question,
                "response": response,
                "retrieved_contexts": contexts,
                "reference": reference,
            })
        except Exception as e:
            logger.error("Failed to run test case '%s': %s", question, e)

    if not processed_cases:
        raise HTTPException(status_code=400, detail="No test cases were successfully executed")

    # Run RAGAS
    eval_results = await run_ragas_eval(processed_cases)
    latest_eval_results = eval_results

    return eval_results


@v1_router.get("/analytics")
async def get_analytics(context: WorkspaceContext = Depends(get_workspace_context)):
    """Retrieve search analytics and document knowledge graph data."""
    try:
        from collections import Counter
        import re

        # 1. Fetch all conversations and messages to compile statistics
        with db.get_connection() as conn:
            # Get all user queries
            user_msgs = conn.execute("SELECT content, created_at FROM messages WHERE role = 'user' AND workspace_id = ?", (context.workspace_id,)).fetchall()
            # Get all assistant responses with metadata
            assistant_msgs = conn.execute("SELECT content, metadata FROM messages WHERE role = 'assistant' AND workspace_id = ?", (context.workspace_id,)).fetchall()
            # Get all document insights
            doc_insights = conn.execute("SELECT source, entities_json, summary FROM document_insights WHERE workspace_id = ?", (context.workspace_id,)).fetchall()

        # Parse user queries for top searched topics (simple keyword frequency)
        stopwords = {"what", "is", "the", "a", "an", "of", "and", "in", "to", "for", "with", "on", "at", "by", "from", "how", "why", "does", "do", "can", "should", "your", "my", "about", "are"}
        words = []
        for row in user_msgs:
            q = row["content"].lower()
            tokens = re.findall(r"\w+", q)
            words.extend([w for w in tokens if w not in stopwords and len(w) > 2])
        
        top_topics = [{"topic": w, "count": count} for w, count in Counter(words).most_common(5)]
        
        # Parse assistant message metadata for most referenced documents
        doc_references = Counter()
        latencies = []
        retrieval_qualities = Counter()
        failed_searches = []
        
        for row in assistant_msgs:
            meta_str = row["metadata"]
            if not meta_str:
                continue
            try:
                meta = json.loads(meta_str)
                # Count citations
                for cite in meta.get("citations", []):
                    # Clean filename if it's a full path
                    base_cite = Path(cite).name
                    doc_references[base_cite] += 1
                
                # Fetch latencies
                obs = meta.get("observability")
                if obs:
                    latencies.append(obs.get("total_latency_sec", 0.0))
                
                # Count retrieval quality
                quality = meta.get("retrieval_quality")
                if quality:
                    retrieval_qualities[quality] += 1
                    
                # Track failed searches (empty context or "bad" quality)
                if not meta.get("citations") or quality == "bad":
                    failed_searches.append({
                        "response_snippet": row["content"][:100] + "...",
                        "quality": quality or "bad"
                    })
            except Exception:
                pass
                
        most_referenced = [{"document": doc, "count": count} for doc, count in doc_references.most_common(5)]
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        
        # 2. Build Document Knowledge Graph
        # Nodes: Documents and Entities
        # Links: Document -> Entity
        nodes = []
        links = []
        node_ids = set()
        
        # Document nodes
        for row in doc_insights:
            doc_name = row["source"]
            doc_id = f"doc_{doc_name}"
            if doc_id not in node_ids:
                nodes.append({
                    "id": doc_id,
                    "label": doc_name,
                    "type": "document"
                })
                node_ids.add(doc_id)
                
            # Parse entities
            entities_str = row["entities_json"] or "[]"
            try:
                entities = json.loads(entities_str)
                # Keep top 5 entities per document to avoid overloading the visual graph
                for ent in entities[:5]:
                    ent_name = ent.get("name")
                    ent_cat = ent.get("category", "General")
                    if not ent_name:
                        continue
                    
                    ent_id = f"ent_{ent_name.lower().replace(' ', '_')}"
                    if ent_id not in node_ids:
                        nodes.append({
                            "id": ent_id,
                            "label": ent_name,
                            "type": "entity",
                            "category": ent_cat
                        })
                        node_ids.add(ent_id)
                    
                    # Create link Document -> Entity
                    links.append({
                        "source": doc_id,
                        "target": ent_id
                    })
            except Exception:
                pass

        return {
            "top_topics": top_topics,
            "most_referenced": most_referenced,
            "average_latency_sec": avg_latency,
            "quality_distribution": dict(retrieval_qualities),
            "failed_searches": failed_searches[:5],
            "knowledge_graph": {
                "nodes": nodes,
                "links": links
            }
        }
    except Exception as e:
        logger.error("Failed to compile analytics: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to compile analytics: {str(e)}")


# In-memory storage for latest 10-Dimension Benchmark results
latest_benchmark_results: Optional[dict] = None


@v1_router.get("/eval/results")
async def get_eval_results():
    """Get the latest stored RAGAS evaluation results."""
    return latest_eval_results


@v1_router.get("/eval/benchmark/suite")
async def run_benchmark_suite_endpoint():
    """Execute the standardized 10-dimension AI Research & Data Analysis Benchmark suite."""
    global latest_benchmark_results
    from eval.benchmark_suite import run_standard_benchmark
    try:
        results = await run_standard_benchmark()
        latest_benchmark_results = results.model_dump()
        return latest_benchmark_results
    except Exception as e:
        logger.error("Benchmark suite execution failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Benchmark failed: {str(e)}")


@v1_router.get("/eval/benchmark/results")
async def get_benchmark_results_endpoint():
    """Fetch the latest stored benchmark results and scoring matrix."""
    if not latest_benchmark_results:
        return {"status": "pending", "message": "No benchmark has been run yet."}
    return latest_benchmark_results


@app.get("/health")
async def health_check(context: WorkspaceContext = Depends(get_workspace_context)):
    """Check connectivity to Ollama models and vector database."""
    import httpx
    
    ollama_ok = False
    chroma_ok = False
    details = {}

    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            if response.status_code == 200:
                ollama_ok = True
                models_info = response.json().get("models", [])
                downloaded_models = [m.get("name") for m in models_info]
                details["ollama_models"] = downloaded_models
                details["llm_model_found"] = any(settings.ollama_llm_model in m for m in downloaded_models)
                details["embed_model_found"] = any(settings.ollama_embed_model in m for m in downloaded_models)
    except Exception as e:
        details["ollama_error"] = str(e)

    # Check ChromaDB
    try:
        list_sources(context)
        chroma_ok = True
    except Exception as e:
        details["chroma_error"] = str(e)

    # Get Workspace Stats
    try:
        workspaces = WorkspaceService.list_workspaces()
        details["workspaces_count"] = len(workspaces)
        details["active_workspace"] = context.workspace_id
    except Exception as e:
        details["workspaces_error"] = str(e)

    # Get Embedding Cache Stats
    try:
        with db.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM embedding_cache").fetchone()
            details["embedding_cache_size"] = row[0] if row else 0
    except Exception as e:
        details["embedding_cache_error"] = str(e)

    # Get Universal Search Telemetry Stats (Module 5 Refinements)
    try:
        search_stats = db.get_search_stats()
        details["universal_search"] = search_stats
    except Exception as e:
        details["universal_search_error"] = str(e)

    # Get Reading Workspace Stats (Module 6 Refinements)
    try:
        reading_stats = db.get_reading_stats()
        details["reading_workspace"] = reading_stats
    except Exception as e:
        details["reading_workspace_error"] = str(e)

    status = "healthy" if (ollama_ok and chroma_ok) else "degraded"
    
    return {
        "status": status,
        "ollama": "ok" if ollama_ok else "error",
        "chromadb": "ok" if chroma_ok else "error",
        "edition": settings.edition,
        "details": details,
    }


app.include_router(v1_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.app_port, reload=True)