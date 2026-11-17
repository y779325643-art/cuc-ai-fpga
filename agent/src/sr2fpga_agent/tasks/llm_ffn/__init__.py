"""Fixed quantized LLM gated-FFN development task, not a qualified benchmark."""

from .task import build_development_task, reference_design

__all__ = ["build_development_task", "reference_design"]
