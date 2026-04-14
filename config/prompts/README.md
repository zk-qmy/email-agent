# Prompt Design
![Prompt Design](assets/doc/prompt_engineering_full_flow.svg)

* `base.py` defines NodePrompt (the 4-part struct) and `PromptConfig` (the container).

* `meeting.py` subclasses `PromptConfig` and fills in one `NodePrompt` per node — each with its own context, task, and critic, but all sharing the same system string via `MEETING_AGENT_SYSTEM`.

* `registry.py` maps workflow names to prompt instances so the router can look up `get_prompts("schedule")` without importing meeting-specific code directly.

* In nodes, the default is a simple function parameter `prompts: PromptConfig = meeting_prompts`. When you need to swap (A/B test, different tone, unit test), you wrap with `functools.partial` in the graph builder — the node function itself never changes.

* `build_messages()` is the only assembly point. It combines all 4 parts into the `[system, user]` message list the LLM receives. The `$variables` in context get substituted from current state values at call time.


The LLM receives that list, applies `with_structured_output()`, and returns a Pydantic model — the output contract is enforced at both the prompt level (critic) and the schema level (Pydantic).

---
# Prompt Design

![Prompt Design](assets/doc/prompt_engineering_full_flow.svg)

## Overview

Prompts are defined as **injectable dependencies** — separated from node logic,
versioned per workflow, and swappable without touching node code.

Each node gets a `NodePrompt` with four parts:

| Part | Purpose | Changes per node? |
|---|---|---|
| `system` | Who the LLM is — persona and hard constraints | No — shared across all nodes in a workflow |
| `context` | Runtime state injected as background (`$vars`) | Yes — different state fields per node |
| `task` | The exact instruction and output contract | Yes — each node does something different |
| `critic` | Binary pre-flight checks before the LLM responds | Yes — each node has different failure modes |

---

## File structure

```
src/core/prompts/
├── __init__.py       exports PromptConfig, NodePrompt, get_prompts
├── base.py           NodePrompt dataclass + PromptConfig base + build_messages()
├── meeting.py        MeetingPrompts — one NodePrompt per meeting workflow node
├── support.py        SupportPrompts — placeholder for future support workflow
└── registry.py       maps workflow name → PromptConfig instance
```

---

## `base.py` — `NodePrompt` and `PromptConfig`

```python
# src/core/prompts/base.py
from __future__ import annotations
from dataclasses import dataclass, field
from string import Template


@dataclass
class NodePrompt:
    """
    A single node's full prompt config.

    system:  Who the LLM is and its hard constraints. Shared across all nodes
             in a workflow — defined once in the workflow's PromptConfig subclass.
    context: Runtime state injected as background info. Supports $variable
             substitution via build_messages(**context_vars).
    task:    The exact instruction for this node. Includes the output contract
             (format, required fields, edge case handling).
    critic:  Binary self-check assertions the LLM applies before responding.
             Each item should correspond to a known failure mode.
    """
    system:  str = ""
    context: str = ""
    task:    str = ""
    critic:  str = ""

    def render(self, part: str, **kwargs) -> str:
        """Fill $variables into a specific part."""
        raw = getattr(self, part, "")
        if not raw:
            raise ValueError(
                f"Prompt part '{part}' is empty in this NodePrompt."
            )
        return Template(raw).substitute(**kwargs)

    def build_messages(self, user_content: str, **context_vars) -> list[dict]:
        """
        Assemble the full message list to send to the LLM.

        Combines system + context + task + critic into the system role.
        Substitutes $variables in context using context_vars.
        Puts user_content in the user role.
        """
        system_parts = []

        if self.system:
            system_parts.append(self.system)

        if self.context:
            rendered_context = (
                Template(self.context).substitute(**context_vars)
                if context_vars
                else self.context
            )
            system_parts.append("--- CONTEXT ---\n" + rendered_context)

        if self.task:
            system_parts.append("--- TASK ---\n" + self.task)

        if self.critic:
            system_parts.append("--- CRITIC ---\n" + self.critic)

        return [
            {"role": "system", "content": "\n\n".join(system_parts)},
            {"role": "user",   "content": user_content},
        ]


@dataclass
class PromptConfig:
    """
    Container of NodePrompts for a whole workflow.
    Each field maps to one node by name.
    Subclass this per workflow and override only the nodes you need.
    """
    classify:        NodePrompt = field(default_factory=NodePrompt)
    extract_meeting: NodePrompt = field(default_factory=NodePrompt)
    ask_missing:     NodePrompt = field(default_factory=NodePrompt)
    draft_email:     NodePrompt = field(default_factory=NodePrompt)
    reply_intent:    NodePrompt = field(default_factory=NodePrompt)

    def get(self, node: str) -> NodePrompt:
        prompt = getattr(self, node, None)
        if prompt is None:
            raise KeyError(
                f"No prompt defined for node '{node}'. "
                f"Add it to your PromptConfig subclass."
            )
        return prompt
```

---

## `meeting.py` — `MeetingPrompts`

```python
# src/core/prompts/meeting.py
from dataclasses import dataclass, field
from src.core.prompts.base import NodePrompt, PromptConfig

MEETING_AGENT_SYSTEM = (
    "You are an AI scheduling assistant that helps users arrange meetings via email.\n"
    "You operate as part of an automated pipeline — each message you receive is a specific task.\n"
    "Always follow the TASK instructions exactly and apply the CRITIC checklist before responding.\n"
    "Never add explanation, preamble, or content outside what the task requires."
)


@dataclass
class MeetingPrompts(PromptConfig):

    classify: NodePrompt = field(default_factory=lambda: NodePrompt(
        system=MEETING_AGENT_SYSTEM,
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
    ))

    extract_meeting: NodePrompt = field(default_factory=lambda: NodePrompt(
        system=MEETING_AGENT_SYSTEM,
        context=(
            "Already extracted so far:\n"
            "  Date: $date\n"
            "  Time: $time\n"
            "  Participants: $participants\n\n"
            "Only extract fields that are missing or updated in the new message."
        ),
        task=(
            "Extract from the latest user message:\n"
            "- date         (prefer YYYY-MM-DD, accept natural language like 'next Monday')\n"
            "- time         (HH:MM 24h format if possible)\n"
            "- participants (list of names or emails)\n\n"
            "Return null for any field not mentioned."
        ),
        critic=(
            "Verify:\n"
            "- No invented values not stated by the user\n"
            "- participants is a list, not a string\n"
            "- Null fields are truly null, not empty string"
        ),
    ))

    ask_missing: NodePrompt = field(default_factory=lambda: NodePrompt(
        system=MEETING_AGENT_SYSTEM,
        context=(
            "Already collected:\n"
            "  Date: $date\n"
            "  Time: $time\n"
            "  Participants: $participants\n\n"
            "Still missing: $missing_fields"
        ),
        task=(
            "Ask the user to provide only the missing fields listed above.\n"
            "Be concise and friendly. Ask for all missing fields in one message."
        ),
        critic=(
            "Verify:\n"
            "- Only asked for fields listed under 'Still missing'\n"
            "- Did not re-ask for already collected fields\n"
            "- Tone is polite and brief"
        ),
    ))

    draft_email: NodePrompt = field(default_factory=lambda: NodePrompt(
        system=MEETING_AGENT_SYSTEM,
        context=(
            "Meeting details:\n"
            "  Date: $date\n"
            "  Time: $time\n"
            "  Participants: $participants"
        ),
        task=(
            "Write a meeting request email using the details above.\n"
            "Format:\n"
            "  Subject: <subject line>\n\n"
            "  <body>\n\n"
            "  Best regards\n\n"
            "Keep the body to 2-3 sentences. Do not add placeholder text."
        ),
        critic=(
            "Verify:\n"
            "- Subject line is present\n"
            "- Date and time from context are in the body\n"
            "- No placeholder text like [Name]\n"
            "- Sign-off is included"
        ),
    ))

    reply_intent: NodePrompt = field(default_factory=lambda: NodePrompt(
        system=MEETING_AGENT_SYSTEM,
        context=(
            "Original meeting request:\n"
            "  Date: $date\n"
            "  Time: $time\n"
            "  Participants: $participants"
        ),
        task=(
            "Classify the recipient's reply as exactly one of:\n"
            "- confirmed  → agreed to the meeting as proposed\n"
            "- negotiate  → wants a different time, date, or format\n"
            "- declined   → refused or unavailable\n\n"
            "Ambiguous replies lean toward 'negotiate' not 'declined'.\n"
            "Return structured output only."
        ),
        critic=(
            "Verify:\n"
            "- Exactly one intent chosen\n"
            "- Structured output only, no explanation"
        ),
    ))


meeting_prompts = MeetingPrompts()
```

---

## `support.py` — `SupportPrompts`

```python
# src/core/prompts/support.py
from dataclasses import dataclass, field
from src.core.prompts.base import NodePrompt, PromptConfig

SUPPORT_AGENT_SYSTEM = (
    "You are an AI support triage assistant.\n"
    "You operate as part of an automated pipeline — each message is a specific task.\n"
    "Always follow the TASK instructions exactly and apply the CRITIC checklist before responding.\n"
    "Never add explanation, preamble, or content outside what the task requires."
)


@dataclass
class SupportPrompts(PromptConfig):

    classify: NodePrompt = field(default_factory=lambda: NodePrompt(
        system=SUPPORT_AGENT_SYSTEM,
        task=(
            "Classify the support request into exactly one of:\n"
            "- bug      → something is broken or behaving incorrectly\n"
            "- feature  → new capability request\n"
            "- question → general inquiry\n\n"
            "If uncertain, choose the closest match."
        ),
        critic=(
            "Verify:\n"
            "- Exactly one label chosen\n"
            "- No explanation or preamble\n"
            "- Structured output only"
        ),
    ))

    # Add more nodes as the support workflow grows:
    # extract_ticket: NodePrompt = ...
    # assign_priority: NodePrompt = ...


support_prompts = SupportPrompts()
```

---

## `registry.py`

```python
# src/core/prompts/registry.py
from src.core.prompts.base import PromptConfig
from src.core.prompts.meeting import meeting_prompts
from src.core.prompts.support import support_prompts

_REGISTRY: dict[str, PromptConfig] = {
    "schedule": meeting_prompts,
    "ticket":   support_prompts,
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
```

---

## `__init__.py`

```python
# src/core/prompts/__init__.py
from src.core.prompts.base import NodePrompt, PromptConfig
from src.core.prompts.meeting import meeting_prompts
from src.core.prompts.support import support_prompts
from src.core.prompts.registry import get_prompts

__all__ = [
    "NodePrompt",
    "PromptConfig",
    "meeting_prompts",
    "support_prompts",
    "get_prompts",
]
```

---

## Usage in nodes

### Default (static import)

```python
# src/nodes/specialized/meeting_nodes.py
from functools import partial
from src.core.prompts.base import PromptConfig
from src.core.prompts.meeting import meeting_prompts


def extract_meeting_info(
    state: AgentState,
    prompts: PromptConfig = meeting_prompts,
) -> dict:
    prompt = prompts.get("extract_meeting")
    messages = prompt.build_messages(
        user_content=state.messages[-1]["content"],
        date=state.meeting.date or "not yet provided",
        time=state.meeting.time or "not yet provided",
        participants=", ".join(state.meeting.participants) or "not yet provided",
    )
    result = (
        get_llm()
        .with_structured_output(MeetingExtraction)
        .invoke(messages)
    )
    ...


def ask_for_missing_info(
    state: AgentState,
    prompts: PromptConfig = meeting_prompts,
) -> dict:
    prompt = prompts.get("ask_missing")
    messages = prompt.build_messages(
        user_content="",
        date=state.meeting.date or "not yet provided",
        time=state.meeting.time or "not yet provided",
        participants=", ".join(state.meeting.participants) or "not yet provided",
        missing_fields=", ".join(state.meeting.missing_fields),
    )
    ...
```

### Injecting a custom prompt (A/B test, different tone, unit test)

```python
# src/workflows/meeting_scheduler.py
from functools import partial
from src.core.prompts.meeting import MeetingPrompts, meeting_prompts
from src.core.prompts.base import NodePrompt

# Override only the node you want to change
custom = MeetingPrompts(
    draft_email=NodePrompt(
        system=MEETING_AGENT_SYSTEM,
        context=(
            "Meeting details:\n"
            "  Date: $date\n"
            "  Time: $time\n"
            "  Participants: $participants"
        ),
        task=(
            "Write a casual, friendly meeting invite.\n"
            "Keep it under 3 sentences. No formal sign-off needed."
        ),
        critic=(
            "Verify:\n"
            "- Tone is casual, not formal\n"
            "- Date and time are included\n"
            "- No placeholder text"
        ),
    )
)

builder.add_node("draft", partial(draft_email, prompts=custom))
builder.add_node("extract_meeting_info", partial(extract_meeting_info, prompts=custom))
```

---

## Adding a new workflow

1. Create `src/core/prompts/new_workflow.py` — subclass `PromptConfig`, define one `NodePrompt` per node.
2. Add `new_workflow_prompts = NewWorkflowPrompts()` at the bottom.
3. Register it in `registry.py`: `"new_workflow": new_workflow_prompts`.
4. Export it from `__init__.py`.
5. Use it in nodes the same way as `meeting_prompts`.