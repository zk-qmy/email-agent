from __future__ import annotations
from dataclasses import dataclass, field
from string import Template


@dataclass
class NodePrompt:
    """
    A single node's full prompt config.
    Each part is optional — only include what the node needs.

    system:  Who the LLM is and its hard constraints.
    context: Runtime state injected as background info ($variables allowed).
    task:    The exact instruction for this node ($variables allowed).
    critic:  Self-check rules the LLM must apply before responding.
    """

    system: str = ""
    context: str = ""
    task: str = ""
    critic: str = ""
    '''
    def __post_init__(self):
        # Ensure all parts are strings (for Template substitution)
        for field_name in ['system', 'context', 'task', 'critic']:
            value = getattr(self, field_name)
            if not isinstance(value, str):
                raise TypeError(
                    f"NodePrompt field '{field_name}' must be a string."
                    f"Got {type(value).__name__} instead."
                    "Did you accidentally pass a Template object?")
    
    def render(self, part: str, **kwargs) -> str:
        """Fill $variables into a specific part."""
        raw = getattr(self, part, "")
        if not raw:
            raise ValueError(f"Prompt part '{part}' is empty in this NodePrompt.")
        return Template(raw).substitute(**kwargs)

    def build_messages(self, user_feedback: str = "", **context_vars) -> list[dict]:
        """
        Assemble the full message list to send to the LLM.
        Combines system + context + task + critic into the system role,
        and puts user_feedback in the user role.
        """
        system_parts = []

        if self.system:
            system_parts.append(str(self.system))

        if self.context:
            rendered_context = (
                Template(self.context).substitute(**context_vars)
                if context_vars
                else self.context
            )
            system_parts.append(
                "--- CONTEXT ---\n" + rendered_context
            )

        if self.task:
            system_parts.append("--- TASK ---\n" + self.task)

        if self.critic:
            system_parts.append("--- CRITIC ---\n" + self.critic)

        return [
            {"role": "system",  "content": "\n\n".join(system_parts)},
            {"role": "user",    "content": user_feedback},
        ]
        
    '''

    def render(self, **kwargs) -> "NodePrompt":
        """Fill $variable placeholders in context with runtime values."""
        return NodePrompt(
            system=self.system,
            context=Template(self.context).safe_substitute(**kwargs),
            task=self.task,
            critic=self.critic,
        )

    def to_prompt(self) -> str:
        """Assemble the full prompt string sent to the LLM."""
        parts = []
        if self.system:
            parts.append(f"SYSTEM:\n{self.system}")
        if self.context:
            parts.append(f"CONTEXT:\n{self.context}")
        if self.task:
            parts.append(f"TASK:\n{self.task}")
        if self.critic:
            parts.append(f"CRITIC:\n{self.critic}")
        return "\n\n".join(parts)


@dataclass
class PromptConfig:
    """
    Container of NodePrompts for a whole workflow.
    Each field = one node's prompt.
    Subclass this per workflow and override only what you need.
    """

    classify: NodePrompt = field(default_factory=NodePrompt)
    extract_meeting_info: NodePrompt = field(default_factory=NodePrompt)
    # ask_missing:     NodePrompt = field(default_factory=NodePrompt)
    draft_email: NodePrompt = field(default_factory=NodePrompt)
    reply_intent: NodePrompt = field(default_factory=NodePrompt)

    def get(self, node: str) -> NodePrompt:
        prompt = getattr(self, node, None)
        if prompt is None:
            raise KeyError(
                f"No prompt defined for node '{node}'",
                "Add it to your PromptConfig subclass.",
            )
        return prompt
