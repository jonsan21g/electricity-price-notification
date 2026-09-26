"""Base interface for all notification dispatchers."""

from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    def send(self, subject: str, message: str) -> bool:
        """
        Send a notification.
        Returns True if successful, False otherwise.
        """
        pass
