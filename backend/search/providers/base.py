from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models.search import SearchRequest, SearchResult, SearchSuggestion
from workspace_service import WorkspaceContext

class SearchProvider(ABC):
    """Abstract base class defining the contract for Universal Search resource providers."""

    @abstractmethod
    async def search(self, req: SearchRequest, context: WorkspaceContext) -> List[SearchResult]:
        """Perform search across provider-specific assets and return normalized results."""
        pass

    @abstractmethod
    async def autocomplete(self, query: str, context: WorkspaceContext) -> List[SearchSuggestion]:
        """Perform title-based autocompletion for provider-specific assets."""
        pass

    @abstractmethod
    async def related(self, asset_id: str, workspace_id: str) -> List[Dict[str, Any]]:
        """Fetch linked/related knowledge items for a provider-specific asset."""
        pass
