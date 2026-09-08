"""Defining receptor-specific failures."""


class ReceptorError(Exception):
    """Representing a safe, user-facing receptor failure."""


class AcquisitionError(ReceptorError):
    """Representing failure to acquire GitHub evidence."""

    def __init__(
        self,
        message: str,
        *,
        category: str = "acquisition_failed",
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.http_status = http_status


class BundleError(ReceptorError):
    """Representing an invalid or incomplete evidence bundle."""


class ContractError(ReceptorError):
    """Representing an unsupported or invalid serialized contract version."""


class ConfigError(ReceptorError):
    """Representing invalid or conflicting declarative configuration."""


class PolicyError(ReceptorError):
    """Representing an invalid comparison regression policy."""


class TrustError(ReceptorError):
    """Representing configuration rejected at a provenance boundary."""
