# src/core/prompts/__init__.py
from config.prompts.base import NodePrompt, PromptConfig
from config.prompts.scheduling import meeting_prompts
#from config.prompts.support import support_prompts
from config.prompts.registry import get_prompts

__all__ = [
    "NodePrompt",
    "PromptConfig",
    "meeting_prompts",
    #"support_prompts",
    "get_prompts",
]