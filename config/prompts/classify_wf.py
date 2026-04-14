# from dataclasses import dataclass, field
# from config.prompts.base import NodePrompt, PromptConfig


# @dataclass
# class ClassifyWorkflowPrompts(PromptConfig):
#     """
#     Prompts for the meeting scheduler workflow.
#     Each field corresponds to one node's prompt.
#     You can add custom fields as needed.
#     The NodePrompt parts (system/context/task/critic) 
#     can use $variable substitution.
#     """

#     classify: NodePrompt = field(
#         default_factory=lambda: NodePrompt(
#             system="",
#             task=(
#                 "Classify the user's request into exactly one of:\n"
#                 "- schedule (meeting scheduling)\n"
#                 "- ticket  (academic accommodation / AA request)\n"
#                 "- chat    (general conversation)\n\n"
#                 "If uncertain, choose the closest match. Return structured output only."
#             ),
#             critic=("""        """),
#         )
#     )


# CLASSIFY_WORKFLOW_PROMPTS = ClassifyWorkflowPrompts()
