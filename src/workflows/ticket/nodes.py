
# Extract info
from typing import Optional, Literal
from langgraph.types import interrupt
from pydantic.v1 import BaseModel

from src.integrations import llm
from src.integrations.llm.client import get_llm
from src.workflows.ticket.state import EmailData, RequestData, TicketState


class AAInfoExtraction(BaseModel):
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    gpa: Optional[float] = None
    credits_completed: Optional[int] = None
    reason: Optional[str] = None
    advisor_email: Optional[str] = None
    registrar_email: Optional[str] = None


def extract_aa_info(state: TicketState):
    """Extract student academic info from the user's message."""
    structured_extractor = get_llm().with_structured_output(AAInfoExtraction)
    result = structured_extractor.invoke([
        {
            "role": "system",
            "content": (
                "Extract academic accommodation (AA) request details from the message.\n"
                "Fields: student_name, student_id, gpa (float), credits_completed (int), "
                "reason for AA, advisor_email, registrar_email.\n"
                "Return None for any field not mentioned."
            ),
        },
        {"role": "user", "content": state.messages[-1]["content"]},
    ])

    # Merge extracted fields onto existing state (don't wipe prior values)
    current = state.ticket_request
    updated = RequestData(
        student_name=result.student_name or current.student_name,
        student_id=result.student_id or current.student_id,
        gpa=result.gpa if result.gpa is not None else current.gpa,
        credits_completed=(
            result.credits_completed
            if result.credits_completed is not None
            else current.credits_completed
        ),
        reason=result.reason or current.reason,
        advisor_email=result.advisor_email or current.advisor_email,
        registrar_email=result.registrar_email or current.registrar_email,
    )
    print(f"[extract_aa_info] student={updated.student_name}, "
          f"gpa={updated.gpa}, credits={updated.credits_completed}")
    return {"ticket_request": updated}

# Validate GPA and credits


# TODO: Add a node to retrieve this
MIN_GPA = 2.0
MIN_CREDITS = 30


def validate_eligibility(state: TicketState):
    """Check whether the student meets minimum GPA and credit requirements."""
    req = state.ticket_request
    notes = []
    eligible = True

    # GPA check
    if req.gpa is None:
        notes.append("GPA not provided")
        eligible = False
    elif req.gpa < MIN_GPA:
        notes.append(f"GPA {req.gpa} is below minimum {MIN_GPA}")
        eligible = False

    # Credits check
    if req.credits_completed is None:
        notes.append("Credits completed not provided")
        eligible = False
    elif req.credits_completed < MIN_CREDITS:
        notes.append(
            f"Credits {req.credits_completed} below minimum {MIN_CREDITS}"
        )
        eligible = False

    eligibility_notes = "; ".join(notes) if notes else "All requirements met"
    print(
        f"[validate_eligibility] eligible={eligible}, notes='{eligibility_notes}'")

    updated = RequestData(
        **req.model_dump(exclude={'is_eligible', 'eligibility_notes'}),
        is_eligible=eligible,
        eligibility_notes=eligibility_notes,
    )
    return {"ticket_request": updated}

# Alert requirement gap


def alert_requirement_gap(state: TicketState):
    """Notify the student they don't meet AA requirements."""
    notes = state.ticket_request.eligibility_notes
    msg = (
        f"⚠️  AA Request Ineligible\n"
        f"Unfortunately you do not currently meet the requirements:\n"
        f"  • {notes}\n\n"
        f"Please contact your advisor to discuss options for improving eligibility."
    )
    print(f"[alert_requirement_gap] {msg}")
    return {"response": msg}

# Draft email to advisor


def draft_aa_email(state: TicketState):
    """Use the LLM to draft a professional AA request email + form summary."""
    req = state.ticket_request

    # Build context from any previous conversation
    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in state.messages
    )

    draft = get_llm().invoke([
        {
            "role": "system",
            "content": (
                "You are an academic assistant helping a student submit an "
                "Academic Accommodation (AA) request.\n"
                "Draft a professional email from the student to their academic advisor "
                "requesting the AA. Also include a brief structured Form Summary at the end.\n"
                "Be concise, polite, and professional."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Student Info:\n"
                f"  Name: {req.student_name or 'N/A'}\n"
                f"  ID: {req.student_id or 'N/A'}\n"
                f"  GPA: {req.gpa}\n"
                f"  Credits Completed: {req.credits_completed}\n"
                f"  Reason for AA Request: {req.reason or 'N/A'}\n"
                f"  Advisor Email: {req.advisor_email or 'N/A'}\n\n"
                f"Conversation Context:\n{history_text}"
            ),
        },
    ])

    # Ensure draft_text is a string, handling cases where draft.content might be a list of parts
    if isinstance(draft.content, list):
        draft_text = "".join([part["text"]
                             for part in draft.content if part.get("text")])
    else:
        draft_text = draft.content

    print(f"[draft_aa_email] draft generated ({len(draft_text)} chars)")
    return {
        "aa_email": EmailData(draft=draft_text),
        "response": draft_text,
    }

# Process student approval


def process_student_approval(state: TicketState):
    """Interrupt to show draft email to student and capture approval."""
    user_input = interrupt({
        "email_draft": state.aa_email.draft,
        "message": "Please review the draft AA request email above. Type: approved / edit",
    })

    content = user_input["content"].lower()
    if any(w in content for w in ["approved", "ok", "looks good", "send it", "yes"]):
        status = "approved"
    elif "edit" in content or "change" in content or "update" in content:
        status = "edit"
    elif "cancel" in content:
        status = "cancelled"
    else:
        status = "pending"

    print(
        f"[process_student_approval] student said: '{content}' → status={status}")
    return {"aa_email": EmailData(approval_status=status)}

# send to advisor (placeholder)


def send_to_advisor(state: TicketState):
    """Placeholder: send the approved AA email to the advisor."""
    advisor = state.ticket_request.advisor_email or "advisor@university.edu"
    print(f"[send_to_advisor] === PLACEHOLDER: email sent to {advisor} ===")
    print(f"  Draft:\n{state.aa_email.draft}")
    return {
        "aa_email": EmailData(status="sent"),
        "response": f"AA request email sent to advisor ({advisor}).",
    }

# wait for reply


def wait_for_advisor_reply(state: TicketState):
    """Placeholder: simulate waiting 48h for advisor reply. No reply received."""
    print("[wait_for_advisor_reply] === PLACEHOLDER: simulating 48h wait — no reply ===")
    return {"aa_email": EmailData(last_reply=None)}


print("wait_for_advisor_reply defined.")
# nudge


def nudge_advisor(state: TicketState):
    """Send a polite follow-up nudge to the advisor."""
    new_count = state.aa_email.nudge_count + 1
    nudge_text = (
        f"Subject: Follow-up: AA Request (Nudge #{new_count})\n\n"
        f"Dear Advisor,\n\n"
        f"I wanted to follow up on my Academic Accommodation request sent earlier.\n"
        f"Could you please review it at your earliest convenience?\n\n"
        f"Thank you,\n"
        f"{state.ticket_request.student_name or 'Student'}"
    )
    print(
        f"[nudge_advisor] === PLACEHOLDER: nudge #{new_count} sent to advisor ===")
    return {
        "aa_email": EmailData(nudge_count=new_count, draft=nudge_text),
        "response": nudge_text,
    }


# send escalation packet
def send_escalation_packet(state: TicketState):
    """Compile and send an escalation packet to the department/dean."""
    msg = (
        f"📦 Escalation Packet Generated\n"
        f"Student: {state.ticket_request.student_name or 'N/A'} "
        f"(ID: {state.ticket_request.student_id or 'N/A'})\n"
        f"Reason: Advisor did not respond after "
        f"{state.aa_email.nudge_count} nudge(s).\n"
        f"Action: Packet forwarded to Department Chair / Dean's office for review."
    )
    print(f"[send_escalation_packet] === PLACEHOLDER: {msg} ===")
    return {"response": msg}

# extract intent from advisor reply


class AdvisorIntentOutput(BaseModel):
    reply_intent: Literal["approved", "needs_info", "rejected"]


def extract_advisor_intent(state: TicketState):
    """Classify the advisor's reply intent."""
    reply = state.aa_email.last_reply
    if not reply:
        return {}

    structured_parser = get_llm().with_structured_output(AdvisorIntentOutput)
    result = structured_parser.invoke([
        {
            "role": "system",
            "content": (
                "You are classifying an advisor's reply to an Academic Accommodation request.\n"
                "Classify as one of:\n"
                "- approved    (advisor approves the AA request)\n"
                "- needs_info  (advisor needs more information before deciding)\n"
                "- rejected    (advisor denies the AA request)\n"
                "Return structured output only."
            ),
        },
        {"role": "user", "content": reply},
    ])
    print(f"[extract_advisor_intent] reply_intent={result.reply_intent}")
    return {"aa_email": EmailData(reply_intent=result.reply_intent)}


# search file history
# TODO: integrate with actual document store and retrieval in production
def search_files_history(state: TicketState):
    """
    Placeholder: AI searches student files / conversation history for
    information the advisor is asking for.

    In production: integrate with a document store (e.g. Google Drive,
    university portal) and use RAG / tool-calling to retrieve relevant docs.
    """
    print("[search_files_history] === PLACEHOLDER: searching student files/history ===")

    # Simulate: 50% chance we find something (toggle for testing)
    # To test the 'not_found' branch, set found = False
    found = True  # <-- change to False to test the ask_student branch

    if found:
        found_text = (
            "Found relevant document: 'Medical Certificate - Spring 2024.pdf'\n"
            "This document supports the student's AA request."
        )
        print(f"[search_files_history] found relevant document")
        return {
            "aa_email": EmailData(search_result="found"),
            "response": found_text,
        }
    else:
        print(f"[search_files_history] no relevant document found")
        return {
            "aa_email": EmailData(search_result="not_found"),
            "response": "No supporting documents found in the student's history.",
        }


# draft info reponse
def draft_info_response(state: TicketState):
    """Draft a supplementary response to the advisor using found documents."""
    req = state.ticket_request

    draft = get_llm().invoke([
        {
            "role": "system",
            "content": (
                "You are an academic assistant. The advisor asked for more information "
                "about the student's AA request. Supporting documents have been found.\n"
                "Draft a concise follow-up email from the student to the advisor, "
                "referencing the supporting document found."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Student: {req.student_name or 'N/A'} (ID: {req.student_id or 'N/A'})\n"
                f"Supporting doc found: {state.response}\n"
                f"Advisor's last reply: {state.aa_email.last_reply}"
            ),
        },
    ])

    draft_text = draft.content
    print(f"[draft_info_response] supplementary draft generated")
    return {
        "aa_email": EmailData(
            draft=draft_text,
            # Reset approval so student reviews the new draft
            approval_status=None,
            # Reset search_result so routing doesn't loop
            search_result=None,
            reply_intent=None,
        ),
        "response": draft_text,
    }


# ask student for info
def ask_student_for_info(state: TicketState):
    """Interrupt: ask the student to provide the additional info the advisor needs."""
    question = (
        "The advisor requires additional information to process your AA request.\n"
        f"Advisor's message: '{state.aa_email.last_reply}'\n\n"
        "Please provide the requested information so I can update the email."
    )
    user_reply = interrupt({"message": question})

    # Append student's reply so draft_info_response can use it
    updated_messages = state.messages + [user_reply]

    # Draft a quick holding response
    draft_text = (
        f"Subject: Re: AA Request — Additional Information\n\n"
        f"Dear Advisor,\n\n"
        f"Thank you for your response. Please see the additional information below:\n\n"
        f"{user_reply['content']}\n\n"
        f"Best regards,\n"
        f"{state.ticket_request.student_name or 'Student'}"
    )

    print(f"[ask_student_for_info] student provided info")
    return {
        "messages": updated_messages,
        "aa_email": EmailData(
            draft=draft_text,
            approval_status=None,
            search_result=None,
            reply_intent=None,
        ),
        "response": question,
    }


# TODO: notify denied

def notify_aa_denied(state: TicketState):
    """Notify student that the advisor denied the AA request."""
    msg = (
        f"❌  AA Request Denied\n"
        f"Your Academic Accommodation request has been reviewed and denied "
        f"by your advisor.\n"
        f"If you believe this decision is incorrect, you may appeal through "
        f"the Dean of Students office."
    )
    print(f"[notify_aa_denied] {msg}")
    return {"response": msg}


# ===REGISTRAR LOOP NODES===
# ONCE THE ADVISOR APPROVES, FORWARD REQUEST TO REGISTRAR/ DEPARTMENT IN CHARGE
# TODO: forward to registrar/department
def forward_to_registrar(state: TicketState):
    """Placeholder: forward the approved AA to the registrar."""
    registrar = state.ticket_request.registrar_email or "registrar@university.edu"
    print(
        f"[forward_to_registrar] === PLACEHOLDER: forwarded to {registrar} ===")
    return {
        "registrar_email": EmailData(status="sent"),
        "response": f"AA request forwarded to registrar ({registrar}) for final processing.",
    }
# TODO: wait for reply


def wait_for_registrar_reply(state: TicketState):
    """Placeholder: simulate 48h wait for registrar reply."""
    print("[wait_for_registrar_reply] === PLACEHOLDER: simulating 48h wait — no reply ===")
    return {"registrar_email": EmailData(last_reply=None)}

# nudge


def nudge_registrar(state: TicketState):
    """Send a follow-up nudge to the registrar."""
    new_count = state.registrar_email.nudge_count + 1
    nudge_text = (
        f"Subject: Follow-up: AA Processing Request (Nudge #{new_count})\n\n"
        f"Dear Registrar,\n\n"
        f"I am following up on the Academic Accommodation request forwarded to "
        f"your office. Could you please provide an update?\n\n"
        f"Thank you,\n"
        f"{state.ticket_request.student_name or 'Student'}"
    )
    print(
        f"[nudge_registrar] === PLACEHOLDER: registrar nudge #{new_count} sent ===")
    return {
        "registrar_email": EmailData(nudge_count=new_count, draft=nudge_text),
        "response": nudge_text,
    }

# escalate to admin


def escalate_to_admin(state: TicketState):
    """Escalate the AA request to university administration."""
    msg = (
        f"🚨 Escalated to Admin\n"
        f"Student: {state.ticket_request.student_name or 'N/A'} "
        f"(ID: {state.ticket_request.student_id or 'N/A'})\n"
        f"The AA request has been escalated to the university administration "
        f"due to an unresolved issue with the registrar's office.\n"
        f"A case manager will contact you within 3 business days."
    )
    print(f"[escalate_to_admin] === PLACEHOLDER: {msg} ===")
    return {"response": msg}

# extract registrar intent


class RegistrarIntentOutput(BaseModel):
    reply_intent: Literal["approved", "issue_detected"]


def extract_registrar_intent(state: TicketState):
    """Classify the registrar's reply: approved or issue_detected."""
    reply = state.registrar_email.last_reply
    if not reply:
        return {}

    structured_parser = get_llm().with_structured_output(RegistrarIntentOutput)
    result = structured_parser.invoke([
        {
            "role": "system",
            "content": (
                "You are classifying a registrar's reply to an Academic Accommodation request.\n"
                "Classify as one of:\n"
                "- approved        (registrar fully processes and approves the request)\n"
                "- issue_detected  (registrar found a problem, error, or missing item)\n"
                "Return structured output only."
            ),
        },
        {"role": "user", "content": reply},
    ])
    print(f"[extract_registrar_intent] reply_intent={result.reply_intent}")
    return {"registrar_email": EmailData(reply_intent=result.reply_intent)}

# #TODO: notify success


def notify_aa_success(state: TicketState):
    """Notify student that their AA request was fully approved."""
    msg = (
        f"🚀 AA Request Approved!\n"
        f"Congratulations {state.ticket_request.student_name or 'Student'}!\n"
        f"Your Academic Accommodation request has been approved by both "
        f"your advisor and the registrar's office.\n"
        f"Your accommodations are now officially in effect."
    )
    print(f"[notify_aa_success] {msg}")
    return {"response": msg}


# TODO: AI self correct
def ai_self_correct(state: TicketState):
    """
    AI attempts to fix the issue identified by the registrar.

    In production: parse the registrar's issue, cross-reference the original
    submission, and generate a corrected version.

    Here we simulate: always 'fixed' for the happy path.
    Toggle `fixed = False` to test the escalation branch.
    """
    print("[ai_self_correct] === PLACEHOLDER: AI attempting to fix registrar issue ===")

    # Simulate fix attempt
    fixed = True  # <-- set to False to test escalation path

    if fixed:
        corrected_draft = (
            f"Subject: Corrected AA Submission\n\n"
            f"Dear Registrar,\n\n"
            f"Thank you for flagging the issue. Please find the corrected "
            f"Academic Accommodation request attached.\n"
            f"The issue has been resolved: "
            f"{state.registrar_email.last_reply or 'see corrections below'}.\n\n"
            f"Best regards,\n"
            f"{state.ticket_request.student_name or 'Student'}"
        )
        print("[ai_self_correct] fix successful")
        return {
            "registrar_email": EmailData(
                self_correct_result="fixed",
                reply_intent=None,   # reset so the loop continues
                last_reply=None,
            ),
            "aa_email": EmailData(draft=corrected_draft),
            "response": corrected_draft,
        }
    else:
        print("[ai_self_correct] could not fix — escalating")
        return {
            "registrar_email": EmailData(self_correct_result="not_fixed"),
            "response": "AI could not automatically resolve the registrar's issue.",
        }
