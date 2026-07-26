import logging
import uuid
import asyncio
from database import db

logger = logging.getLogger("neurasearch.core.telemetry")

def log_telemetry_event(
    type: str,
    workspace_id: str,
    session_id: str,
    duration_ms: int,
    metadata: dict
) -> str:
    """Logs a generic telemetry event and persists it to the database.

    Runs as a non-blocking background task.
    """
    event_id = uuid.uuid4().hex
    logger.info(
        "Telemetry [%s] - Session: %s - Workspace: %s - Duration: %d ms",
        type, session_id, workspace_id, duration_ms
    )
    
    # Run the blocking DB write in a separate thread pool to preserve loop performance
    try:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(
            None,
            db.save_telemetry_event,
            event_id,
            type,
            workspace_id,
            session_id,
            duration_ms,
            metadata
        )
    except RuntimeError:
        # Fallback for synchronous execution contexts
        db.save_telemetry_event(event_id, type, workspace_id, session_id, duration_ms, metadata)
        
    return event_id
