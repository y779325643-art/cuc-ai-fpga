"""SR2FPGA lightweight data generation agent."""

from sr2fpga_agent.models import GeneratedProject, PlatformProfile, ProjectRequest
from sr2fpga_agent.project_generator import ProjectGenerator
from sr2fpga_agent.agent import DataGenerationAgent
from sr2fpga_agent.generation import DirectProjectGenerator
from sr2fpga_agent.providers import OpenAICompatibleClient, OpenAICompatibleConfig
from sr2fpga_agent.repair import ProjectRepairer, SystemHisRepairer

# Compatibility alias for the former provider-specific root export.
DeepSeekProjectGenerator = DirectProjectGenerator

__all__ = [
    "DataGenerationAgent",
    "DirectProjectGenerator",
    "DeepSeekProjectGenerator",
    "GeneratedProject",
    "OpenAICompatibleClient",
    "OpenAICompatibleConfig",
    "PlatformProfile",
    "ProjectRepairer",
    "ProjectGenerator",
    "ProjectRequest",
    "SystemHisRepairer",
]
