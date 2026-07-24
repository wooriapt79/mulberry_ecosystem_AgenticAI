"""Provider-neutral boundaries for production security adapters."""

from typing import Protocol


class SecretProvider(Protocol):
    def get_secret(self, name: str) -> str:
        """Return a runtime secret without persisting it in application data."""


class SecondFactorProvider(Protocol):
    def begin(self, user_id: str) -> str:
        """Create an expiring MFA or passkey challenge."""

    def verify(self, user_id: str, challenge_id: str, response: str) -> bool:
        """Verify a challenge without exposing credential material."""
