"""Step 1 of the write path: transcript -> structured facts."""
import llm

SYSTEM = (
    "You extract structured facts from meeting transcripts for a meeting-memory "
    "system. Use ONLY what is stated. Always name the party (person and company) "
    "behind every priority, concern and commitment. Dates must be YYYY-MM-DD or null."
)

SCHEMA = """{
  "summary": "two sentences",
  "audience": "client_facing" or "internal_only",
  "attendees": ["Name (Company)"],
  "decisions": [{"decision": "", "made_by": ""}],
  "priorities": [{"party": "", "priority": "", "strength": "top|high|medium|low", "note": ""}],
  "commitments": [{"owner": "", "task": "", "due": null, "made_to": ""}],
  "concerns": [{"party": "", "concern": "", "answered": false}],
  "pricing": [{"detail": ""}],
  "open_questions": [""]
}"""


def extract_meeting(transcript: str, title: str, date: str, client_name: str, our_company: str) -> dict:
    user = (
        f"Our company: {our_company}\nClient: {client_name}\n"
        f"Meeting: {title} on {date}\n\n"
        "'internal_only' means nobody from the client was present.\n\n"
        f"TRANSCRIPT:\n{transcript}\n\nReturn JSON in exactly this shape:\n{SCHEMA}"
    )
    data = llm.chat_json(SYSTEM, user)
    # make sure every key exists so later code never crashes
    for key in ("decisions", "priorities", "commitments", "concerns", "pricing", "open_questions", "attendees"):
        data.setdefault(key, [])
    data.setdefault("summary", "")
    data.setdefault("audience", "unknown")
    return data
