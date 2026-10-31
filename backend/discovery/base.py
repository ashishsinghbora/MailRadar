from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DiscoveredProject(BaseModel):
    name: str
    full_name: str
    owner: str
    description: Optional[str] = None
    stars_count: int = 0
    forks_count: int = 0
    language: Optional[str] = None
    topics: List[str] = []
    repository_url: str
    homepage_url: Optional[str] = None
    contributing_url: Optional[str] = None
    last_activity_at: Optional[str] = None


class DiscoveredSourceContent(BaseModel):
    source_url: str
    source_category: str
    content: str
    metadata: Dict[str, Any] = {}


class BaseSourceAdapter(ABC):
    @abstractmethod
    async def search(self, query: str, **kwargs) -> List[DiscoveredProject]:
        """Search projects matching criteria."""
        pass

    @abstractmethod
    async def fetch_sources(self, project: DiscoveredProject) -> List[DiscoveredSourceContent]:
        """Fetch permitted official source documents (README, CONTRIBUTING, Website)."""
        pass
