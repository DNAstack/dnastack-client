from abc import ABC, abstractmethod
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field
import logging

from dnastack.common.tracing import Span
from dnastack.http.client_factory import HttpClientFactory


class CloudProvider(str, Enum):
    GCP = "gcp"


class CloudMetadataProvider(ABC):
    """Abstract base class for cloud metadata providers."""

    timeout: int
    _logger: logging.Logger

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self._logger = logging.getLogger(type(self).__name__)

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this cloud provider's metadata service is available."""
        pass

    @abstractmethod
    def get_identity_token(self, audience: str, trace_context: Span) -> Optional[str]:
        """Fetch an identity token from the cloud metadata service."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this cloud provider."""
        pass


class GCPMetadataProvider(CloudMetadataProvider):
    """Google Cloud Platform metadata provider."""

    _METADATA_BASE_URL = 'http://metadata.google.internal/computeMetadata/v1'
    _IDENTITY_ENDPOINT = '/instance/service-accounts/default/identity'
    _METADATA_FLAVOR = 'Google'

    @property
    def name(self) -> str:
        return CloudProvider.GCP.value

    def is_available(self) -> bool:
        """Check if GCP metadata service is available."""
        try:
            with HttpClientFactory.make() as http_session:
                response = http_session.get(
                    f'{self._METADATA_BASE_URL}/project/project-id',
                    headers={'Metadata-Flavor': self._METADATA_FLAVOR},
                    timeout=1
                )
                return response.ok
        except Exception:
            return False

    def get_identity_token(self, audience: str, trace_context: Span) -> Optional[str]:
        """Fetch GCP identity token from metadata service.
           '&format=full' ensures we get email in response"""
        url = f'{self._METADATA_BASE_URL}{self._IDENTITY_ENDPOINT}?audience={audience}&format=full'

        try:
            with HttpClientFactory.make() as http_session:
                response = http_session.get(
                    url,
                    headers={'Metadata-Flavor': self._METADATA_FLAVOR},
                    timeout=self.timeout
                )

                if response.ok:
                    token = response.text.strip()
                    self._logger.debug(f'Successfully fetched GCP identity token for audience: {audience}')
                    return token
                else:
                    self._logger.warning(f'GCP metadata service returned {response.status_code}: {response.text}')
                    return None

        except Exception as e:
            self._logger.warning(f'Failed to fetch GCP identity token: {e}')
            return None


class CloudMetadataConfig(BaseModel):
    """Configuration model for cloud metadata provider."""
    timeout: int = Field(5, ge=1, le=30, description="Timeout for metadata service request (1-30 seconds).")


class CloudProviderFactory:
    """Factory for creating cloud metadata providers."""
    _providers = {
        CloudProvider.GCP: GCPMetadataProvider,
    }

    @classmethod
    def create(cls, provider: CloudProvider, config: CloudMetadataConfig) -> CloudMetadataProvider:
        """Create a cloud metadata provider instance."""
        provider_class = cls._providers.get(provider)
        if not provider_class:
            raise ValueError(f'Unsupported cloud provider: {provider}')
        return provider_class(timeout=config.timeout)

    @classmethod
    def detect_provider(cls, config: CloudMetadataConfig) -> Optional[CloudMetadataProvider]:
        """Auto-detect the current cloud provider by checking all available providers."""
        for provider_type in cls._providers.keys():
            try:
                provider = cls.create(provider_type, config)
                if provider.is_available():
                    return provider
            except Exception:
                # Skip providers that fail to initialize or check availability
                continue
        return None
