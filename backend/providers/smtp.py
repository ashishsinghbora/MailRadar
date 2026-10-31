import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
import uuid
from backend.core.config import settings
from backend.providers.base import EmailProvider, DeliveryResult


class SmtpProvider(EmailProvider):
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        from_email: Optional[str] = None
    ):
        self.host = host or settings.smtp_host
        self.port = port or settings.smtp_port
        self.user = user or settings.smtp_user
        self.password = password or settings.smtp_password
        self.use_tls = use_tls if use_tls is not None else settings.smtp_use_tls
        self.from_email = from_email or settings.smtp_from_email

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
        msg_id = f"smtp-{uuid.uuid4()}"
        sender = from_email or self.from_email

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to_email
        msg["Message-ID"] = f"<{msg_id}@{self.host}>"

        if headers:
            for k, v in headers.items():
                msg[k] = v

        # Plain text
        part_text = MIMEText(body_markdown, "plain")
        msg.attach(part_text)

        # HTML
        if body_html:
            part_html = MIMEText(body_html, "html")
            msg.attach(part_html)

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10.0) as server:
                if self.use_tls:
                    server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(sender, [to_email], msg.as_string())

            return DeliveryResult(
                success=True,
                status="SENT",
                provider_message_id=msg_id,
                raw_payload={"to": to_email, "from": sender, "id": msg_id}
            )
        except smtplib.SMTPRecipientsRefused as e:
            return DeliveryResult(
                success=False,
                status="BOUNCED",
                provider_message_id=msg_id,
                error_message=f"Recipient refused: {str(e)}"
            )
        except Exception as e:
            return DeliveryResult(
                success=False,
                status="FAILED",
                provider_message_id=msg_id,
                error_message=f"SMTP transport error: {str(e)}"
            )
