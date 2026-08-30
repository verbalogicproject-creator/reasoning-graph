"""Provider-neutral contracts for observable extended-thinking integrations.

The adapters in this package build request dictionaries and normalize recorded
responses.  They do not import provider SDKs or make network calls.
"""

from .anthropic import ANTHROPIC_PROFILE, build_anthropic_request, normalize_anthropic_response
from .common import ProviderProfile, ProviderTurnRecord
from .gemini import GEMINI_PROFILE, build_gemini_request, normalize_gemini_response
from .openai import OPENAI_PROFILE, build_openai_request, normalize_openai_response

__all__ = [
    "ANTHROPIC_PROFILE",
    "GEMINI_PROFILE",
    "OPENAI_PROFILE",
    "ProviderProfile",
    "ProviderTurnRecord",
    "build_anthropic_request",
    "build_gemini_request",
    "build_openai_request",
    "normalize_anthropic_response",
    "normalize_gemini_response",
    "normalize_openai_response",
]
