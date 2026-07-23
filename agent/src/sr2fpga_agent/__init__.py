"""SR2FPGA lightweight data generation agent."""

from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.deepseek import (
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
