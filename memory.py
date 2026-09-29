"""Everything that talks to Hindsight lives here.

Hindsight has three main operations:
  retain()  -> store something in a memory bank
  recall()  -> search the bank
  reflect() -> ask the bank a question and get a reasoned answer
We use ONE bank per client so their history stays separate.
"""
import re
from datetime import datetime

import config

MISSION = (
    "I am a meeting-prep assistant. For each client I track what every party "
    "prioritizes, decisions made, commitments (owner and due date), concerns, and "
    "pricing. When priorities or decisions change over time I keep the history and "
    "flag conflicts, especially when an internal decision was never communicated "
    "to the client."
)

_client = None


def get_client():
    global _client
    if _client is None:
        from hindsight_client import Hindsight  # imported lazily
        kwargs = {"base_url": config.HINDSIGHT_BASE_URL, "timeout": 120.0}
        if config.HINDSIGHT_API_KEY:
            kwargs["api_key"] = config.HINDSIGHT_API_KEY
        _client = Hindsight(**kwargs)
    return _client


def bank_id_for(client_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", client_name.lower()).strip("-")
    return f"memorymeet-{slug}"


def ensure_bank(client_name: str) -> str:
    bank_id = bank_id_for(client_name)
    try:
        get_client().create_bank(
            bank_id=bank_id, name=f"MemoryMeet - {client_name}", mission=MISSION
        )
    except Exception:
        pass  # most likely the bank already exists, which is fine
    return bank_id


def extraction_to_note(title: str, date: str, ex: dict) -> str:
    """Turn the structured extraction into a clean, dated text note for Hindsight."""
    lines = [
        f"Meeting: {title}",
        f"Date: {date}",
        f"Audience: {ex.get('audience', 'unknown')}",
        f"Attendees: {', '.join(ex.get('attendees', []))}",
        f"Summary: {ex.get('summary', '')}",
    ]
    for d in ex.get("decisions", []):
        lines.append(f"Decision (by {d.get('made_by', '?')}): {d.get('decision', '')}")
    for p in ex.get("priorities", []):
        lines.append(
            f"Priority of {p.get('party', '?')} [{p.get('strength', '?')}]: "
            f"{p.get('priority', '')}. {p.get('note', '')}".strip()
        )
    for c in ex.get("commitments", []):
        lines.append(
            f"Commitment: {c.get('owner', '?')} will {c.get('task', '')} "
            f"(due {c.get('due') or 'no date'}, to {c.get('made_to') or 'n/a'})"
        )
    for c in ex.get("concerns", []):
        status = "answered" if c.get("answered") else "NOT yet answered"
        lines.append(f"Concern from {c.get('party', '?')}: {c.get('concern', '')} ({status})")
    for p in ex.get("pricing", []):
        lines.append(f"Pricing: {p.get('detail', '')}")
    for q in ex.get("open_questions", []):
        lines.append(f"Open question: {q}")
    return "\n".join(lines)


def retain_meeting(client_name: str, meeting_id: str, title: str, date: str, ex: dict):
    """Store one meeting in Hindsight, stamped with the meeting's real date."""
    bank_id = ensure_bank(client_name)
    get_client().retain(
        bank_id=bank_id,
        content=extraction_to_note(title, date, ex),
        context=f"Meeting with {client_name}: {title}",
        timestamp=datetime.fromisoformat(date),
        document_id=meeting_id,
        metadata={"meeting_id": meeting_id, "date": date},
        retain_async=False,  # wait until stored so the next recall can see it
    )


def recall_history(client_name: str, queries: list, max_tokens: int = 3000) -> list:
    """Run several searches and return de-duplicated memories: [{'text','type'}]."""
    bank_id = bank_id_for(client_name)
    seen, out = set(), []
    for q in queries:
        result = get_client().recall(
            bank_id=bank_id, query=q, max_tokens=max_tokens, budget="mid"
        )
        for r in result.results:
            if r.text not in seen:
                seen.add(r.text)
                out.append({"text": r.text, "type": getattr(r, "type", "memory")})
    return out


def ask_memory(client_name: str, question: str, context: str = "preparing for a client meeting") -> str:
    answer = get_client().reflect(
        bank_id=bank_id_for(client_name), query=question, budget="low", context=context
    )
    return answer.text
