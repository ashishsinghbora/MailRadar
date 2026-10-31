import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from backend.providers.base import EmailProvider, DeliveryResult


class SandboxProvider(EmailProvider):
    """
    Safe Sandbox delivery provider.
    Simulates successful email dispatch and stores sent payloads in memory/history
    for end-to-end verification and testing with zero network egress.
    """
    _sent_box: List[Dict[str, Any]] = []

    def __init__(self, simulate_bounce: bool = False):
        self.simulate_bounce = simulate_bounce

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
        msg_id = f"sandbox-{uuid.uuid4()}"

        record = {
            "message_id": msg_id,
            "to_email": to_email,
            "from_email": from_email or "outreach@mailradar.dev",
            "subject": subject,
            "body_markdown": body_markdown,
            "body_html": body_html,
            "headers": headers or {},
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._sent_box.append(record)

        if self.simulate_bounce:
            return DeliveryResult(
                success=False,
                status="BOUNCED",
                provider_message_id=msg_id,
                error_message="Simulated 550 Mailbox does not exist (Sandbox)",
                raw_payload=record
            )

        return DeliveryResult(
            success=True,
            status="SENT",
            provider_message_id=msg_id,
            raw_payload=record
        )

    @classmethod
    def get_sent_messages(cls) -> List[Dict[str, Any]]:
        return list(cls._sent_box)

    @classmethod
    def clear(cls) -> None:
        cls._sent_box.clear()
