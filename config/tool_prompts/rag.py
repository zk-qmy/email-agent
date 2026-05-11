from dataclasses import dataclass, field
from config.tool_prompts.base import NodePrompt, PromptConfig
from config.tool_prompts.system_prompt import SystemPrompt
from datetime import datetime


@dataclass
class RAGPrompts(PromptConfig):
    """
    Prompts for RAG
    Each field corresponds to one node's prompt.
    You can add custom fields as needed.
    The NodePrompt parts (system/context/task/critic) can use $variable substitution.
    """

    suggest_department: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            context=(
                "Department guide context:\n"
                "$context\n\n"
                "Student request:\n"
                "$student_request\n"
            ),
            task=(
                "Analyze the STUDENT REQUEST using ONLY the provided CONTEXT.\n\n"

                "Determine:\n"
                "- which department should handle the request\n"
                "- the appropriate contact information if available\n"
                "- the expected reply or resolution time\n"
                "- why this department is responsible\n"
                "- any helpful notes or guidance for the student\n\n"

                "Rules:\n"
                "- Use ONLY information explicitly found in the CONTEXT\n"
                "- Do NOT invent departments, contacts, or timelines\n"
                "- If information is missing, return null or 'Not found in guide'\n"
                "- Keep explanations concise and student-friendly\n"
                "- Output must be valid JSON only\n\n"

                "Return JSON format:\n"
                "{\n"
                '  "department": "<department name>",\n'
                '  "contact": "<email, office, or Not found in guide>",\n'
                '  "reply_time": "<expected response time>",\n'
                '  "reason": "<why this department matches>",\n'
                '  "notes": "<extra guidance or next steps>"\n'
                "}"
            ),
            critic=(
                "Verify:\n"
                "- Department selection matches the guide context\n"
                "- No information is fabricated\n"
                "- Reply time comes directly from the guide if available\n"
                "- Contact information exists in the context\n"
                "- Reason is concise and logical\n"
                "- Output is valid JSON only\n"
            ),
        )
    )

    
    ask_guide: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            context=(
                "Department guide context:\n"
                "$context\n\n"
                "Student question:\n"
                "$question\n"
            ),
            task=(
                "Answer the STUDENT QUESTION using ONLY the provided CONTEXT.\n\n"

                "Rules:\n"
                "- Do NOT use outside knowledge\n"
                "- If the answer cannot be found in the context, clearly state that\n"
                "- Keep the answer concise and accurate\n"
                "- Include the related section or department if identifiable\n"
                "- Output must be valid JSON only\n\n"

                "Return JSON format:\n"
                "{\n"
                '  "answer": "<direct answer>",\n'
                '  "source_section": "<related section or department>",\n'
                '  "found_in_guide": true\n'
                "}\n\n"

                "If the information is NOT found:\n"
                "{\n"
                '  "answer": "Information not found in the guide.",\n'
                '  "source_section": null,\n'
                '  "found_in_guide": false\n'
                "}"
            ),
            critic=(
                "Verify:\n"
                "- Answer is supported by the provided context\n"
                "- No fabricated information exists\n"
                "- source_section is accurate if available\n"
                "- found_in_guide is correct\n"
                "- Output is valid JSON only\n"
            ),
        )
    )


    search_docs: NodePrompt = field(
        default_factory=lambda: NodePrompt(
            system=SystemPrompt.system_prompt,
            context=(
                "Guide context:\n"
                "$context\n\n"
                "Search query:\n"
                "$query\n"
            ),
            task=(
                "Answer the SEARCH QUERY using ONLY the provided CONTEXT.\n\n"

                "Rules:\n"
                "- Do NOT use outside knowledge\n"
                "- If the answer cannot be found in the context, clearly state that\n"
                "- Keep the answer concise and accurate\n"
                "- Include the related section or department if identifiable\n"
                "- Output must be valid JSON only\n\n"

                "Return JSON format:\n"
                "{\n"
                '  "answer": "<direct answer>",\n'
                '  "source_section": "<related section or department>",\n'
                '  "found_in_guide": true\n'
                "}\n\n"

                "If the information is NOT found:\n"
                "{\n"
                '  "answer": "Information not found in the guide.",\n'
                '  "source_section": null,\n'
                '  "found_in_guide": false\n'
                "}"
            ),
            critic=(
                "Verify:\n"
                "- Answer is supported by the provided context\n"
                "- No fabricated information exists\n"
                "- source_section is accurate if available\n"
                "- found_in_guide is correct\n"
                "- Output is valid JSON only\n"
            ),
        )
    )


rag_prompts = RAGPrompts()