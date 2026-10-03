"""Single-degree-of-freedom response and response spectra tools."""

from .newmark import ResponseHistory, compute_response
from .spectra import SpectrumResult, compute_spectra

__all__ = [
    "ResponseHistory",
    "compute_response",
    "SpectrumResult",
    "compute_spectra",
]
