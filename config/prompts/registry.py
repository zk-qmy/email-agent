# src/core/prompts/registry.py
from config.prompts.base import PromptConfig
from config.prompts.scheduling import meeting_prompts
from config.prompts.ticket import ticket_prompts
from config.prompts.shared import shared_prompts

_REGISTRY: dict[str, PromptConfig] = {
    "shared": shared_prompts,
    "schedule": meeting_prompts,
    "ticket":   ticket_prompts,
}


def get_prompts(workflow: str) -> PromptConfig:
    """Look up the prompt config for a workflow name.

    Used by the router to resolve prompts without importing
    workflow-specific modules directly.
    """
    if workflow not in _REGISTRY:
        raise KeyError(
            f"No prompts registered for workflow '{workflow}'. "
            f"Add it to _REGISTRY in registry.py."
        )
    return _REGISTRY[workflow]
