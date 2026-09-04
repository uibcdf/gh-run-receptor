"""Defining receptor-specific failures."""


class ReceptorError(Exception):
    """Representing a safe, user-facing receptor failure."""


class AcquisitionError(ReceptorError):
    """Representing failure to acquire GitHub evidence."""


class BundleError(ReceptorError):
    """Representing an invalid or incomplete evidence bundle."""
