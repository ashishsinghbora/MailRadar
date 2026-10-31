from backend.core.config import settings
from backend.providers.base import EmailProvider
from backend.providers.sandbox import SandboxProvider
from backend.providers.smtp import SmtpProvider


class ProviderRegistry:
    @staticmethod
    def get_provider(provider_name: str = None) -> EmailProvider:
        name = (provider_name or settings.delivery_provider).lower()
        if name == "smtp":
            return SmtpProvider()
        return SandboxProvider()
