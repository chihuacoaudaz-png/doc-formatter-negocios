"""Format-independent document parsing."""
from .compiler import parse_document
from .model import InvalidSource, to_data

__all__ = ["parse_document", "InvalidSource", "to_data"]
