from __future__ import annotations


class DesignAgentsError(Exception):
    """Base error for the VNext runtime."""


class RegistryError(DesignAgentsError):
    """Raised when registry assets cannot be scanned or resolved."""


class GovernanceError(DesignAgentsError):
    """Raised when governance policies fail."""


class BoundaryViolationError(DesignAgentsError):
    """Raised when a hard runtime boundary is crossed."""
