from config.prompts.base import PromptConfig, NodePrompt
from dataclasses import dataclass, field


@dataclass
class RouterPrompts(PromptConfig):
    classify_workflow: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system="You are a router. Classify the user's request.",
            task=(
                "Classify the user's request into exactly one of:\n"
                "- schedule  → meeting or calendar related\n"
                "- ticket    → bug report, support issue, complaint\n"
                "- chat      → anything else\n\n"
                "If uncertain, choose the closest match."
            ),
            critic=(
                "Verify:\n"
                "- Exactly one label chosen\n"
                "- No explanation or preamble\n"
                "- Structured output only"
            ),
        )
    )


shared_prompts = RouterPrompts()
