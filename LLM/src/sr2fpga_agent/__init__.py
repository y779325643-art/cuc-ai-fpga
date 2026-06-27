"""SR2FPGA lightweight data generation agent."""

from LLM.src.sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from LLM.src.sr2fpga_agent.project_generator import ProjectGenerator
from LLM.src.sr2fpga_agent.agent import DataGenerationAgent
from LLM.src.sr2fpga_agent.deepseek import (
    DeepSeekProjectGenerator,
    OpenAICompatibleClient,
    OpenAICompatibleConfig,
)

__all__ = [
    "DataGenerationAgent",
    "DeepSeekProjectGenerator",
    "GeneratedProject",
    "OpenAICompatibleClient",
    "OpenAICompatibleConfig",
    "PlatformProfile",
    "ProjectGenerator",
    "ProjectRequest",
]
