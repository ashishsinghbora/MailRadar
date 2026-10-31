from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel


class DeliveryResult(BaseModel):
    success: bool
    status: str  # SENT, FAILED, BOUNCED
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    raw_payload: Dict[str, Any] = {}


class EmailProvider(ABC):
    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_markdown: str,
        body_html: Optional[str] = None,
        from_email: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        pass
