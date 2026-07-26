class NeuraSearchError(Exception):
    """Base exception for all NeuraSearch domain errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class WorkspaceError(NeuraSearchError):
    def __init__(self, message: str, code: str = "WORKSPACE_ERROR"):
        super().__init__(message, code)


class RetrievalError(NeuraSearchError):
    def __init__(self, message: str, code: str = "RETRIEVAL_ERROR"):
        super().__init__(message, code)


class ResearchError(NeuraSearchError):
    def __init__(self, message: str, code: str = "RESEARCH_ERROR"):
        super().__init__(message, code)


class ComputationError(NeuraSearchError):
    def __init__(self, message: str, code: str = "COMPUTATION_ERROR"):
        super().__init__(message, code)


class AuthenticationError(NeuraSearchError):
    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        super().__init__(message, code)


class IngestionError(NeuraSearchError):
    def __init__(self, message: str, code: str = "INGESTION_ERROR"):
        super().__init__(message, code)


class KnowledgeError(NeuraSearchError):
    """Base exception for all Knowledge Hub errors."""
    def __init__(self, message: str, code: str = "KNOWLEDGE_ERROR"):
        super().__init__(message, code)


class KnowledgeConflictError(KnowledgeError):
    """Raised when optimistic locking detects stale updates."""
    def __init__(self, message: str = "Knowledge item has been modified by another process.", code: str = "KNOWLEDGE_CONFLICT"):
        super().__init__(message, code)
