"""The READ path: recalled memories -> what changed -> briefing."""
from datetime import date

import llm
import memory

# The searches we run against Hindsight before every meeting. Several focused
# queries beat one vague query.
RECALL_QUERIES = [
    "What does each party prioritize and how have priorities changed?",
    "Decisions made, including internal decisions the client may not know about",
    "Commitments, promises, deliverables and due dates",
    "Concerns and open questions from the client",
    "Pricing, discounts and contract terms discussed",
]


def format_memories(memories: list) -> str:
    return "\n".join(f"- [{m['type']}] {m['text']}" for m in memories)


def gather_history(client_name: str) -> list:
    return memory.recall_history(client_name, RECALL_QUERIES)


CHANGE_SYSTEM = (
    "You are a sharp chief-of-staff analyst. You receive memory facts about one client "
    "relationship (each note has a Date). Order them by date, then find what CHANGED. "
    "Only report things supported by the facts. Never invent."
)

CHANGE_RULES = """Change types:
- priority_shift: a party's priority changed or was deprioritized
- contradiction: two facts conflict (e.g. price promised vs internal price floor)
- unresolved_commitment / slipped_deadline: promised item overdue or not delivered
- unanswered_concern: a concern raised and never answered
- expectation_gap: an INTERNAL decision the client was never told about, while the
  client may still expect the old plan

Return JSON: {"changes":[{"type":"","severity":"high|medium|low","title":"",
"what_changed":"","evidence":["YYYY-MM-DD: short paraphrase"],"affected":"who or what is affected"}]}
Order by severity. Maximum 6 changes. If nothing changed, return {"changes":[]}."""


def detect_changes(memories: list, upcoming: dict) -> list:
    user = (
        f"Today's date: {date.today().isoformat()}\n"
        f"Upcoming meeting: {upcoming['title']} on {upcoming['date']} with {upcoming['attendees']}\n\n"
        f"MEMORY FACTS:\n{format_memories(memories)}\n\n{CHANGE_RULES}"
    )
    data = llm.chat_json(CHANGE_SYSTEM, user)
    return data.get("changes", [])


BRIEF_SYSTEM = (
    "You write concise pre-meeting briefings for a busy account manager. "
    "Be specific, cite dates, no fluff."
)


def generate_briefing(changes: list, memories: list, upcoming: dict) -> str:
    user = (
        f"Upcoming meeting: {upcoming['title']} on {upcoming['date']}\n"
        f"Attendees: {upcoming['attendees']}\nAgenda: {upcoming['agenda']}\n\n"
        f"DETECTED CHANGES (JSON): {changes}\n\n"
        f"SUPPORTING MEMORY:\n{format_memories(memories)}\n\n"
        "Write the briefing in markdown with EXACTLY these sections and under 350 words:\n"
        "## Snapshot\n(2-3 sentences)\n"
        "## What changed\n(bullets, with dates)\n"
        "## What may be affected\n(who might still hold an old expectation, and the risk)\n"
        "## Clarify in this meeting\n(3-4 specific questions to ask)\n"
        "## Recommended next actions\n(numbered, with owners if known)"
    )
    return llm.chat(BRIEF_SYSTEM, user, temperature=0.3)


def generic_briefing(upcoming: dict) -> str:
    """The 'without memory' baseline used for the before/after demo."""
    user = (
        f"Upcoming meeting: {upcoming['title']} on {upcoming['date']}\n"
        f"Attendees: {upcoming['attendees']}\nAgenda: {upcoming['agenda']}\n\n"
        "You have NO history about this client. Write a short generic prep briefing "
        "(under 150 words) with an agenda summary and a few standard questions."
    )
    return llm.chat(BRIEF_SYSTEM, user, temperature=0.3)
