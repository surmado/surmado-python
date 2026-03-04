"""
Surmado Python SDK

Official Python client for Surmado - the anti-dashboard marketing intelligence engine.

Installation:
    pip install surmado

Quick Start:
    >>> from surmado import Surmado
    >>> client = Surmado()  # reads SURMADO_API_KEY from env
    >>>
    >>> # Run a Full Analysis Bundle (Site Audit + AI Visibility + Strategy)
    >>> result = client.bundle(
    ...     brand_slug="acme_corp",
    ...     email="you@example.com"
    ... )
    >>>
    >>> # Or run individual reports
    >>> report = client.signal(
    ...     url="https://example.com",
    ...     brand_name="Example",
    ...     email="you@example.com",
    ...     industry="E-commerce",
    ...     location="United States",
    ...     persona="Small business owners",
    ...     pain_points="Finding reliable vendors",
    ...     brand_details="Affordable solutions",
    ...     direct_competitors="Competitor A, Competitor B"
    ... )

Documentation: https://surmado.com/docs
API Reference: https://help.surmado.com/docs/api-reference/
"""

from .client import (
    Surmado,
    SurmadoError,
    AuthenticationError,
    InsufficientCreditsError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    __version__,
)

__all__ = [
    "Surmado",
    "SurmadoError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "__version__",
]

