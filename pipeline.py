"""Glue for the WRITE path: transcript -> extract -> retain in Hindsight."""
import json
import os

import extractor
import memory

DEMO_FILE = os.path.join(os.path.dirname(__file__), "data", "meetings.json")


def ingest_meeting(client_name, our_company, title, date, transcript, meeting_id=None):
    meeting_id = meeting_id or f"{date}-{title}".lower().replace(" ", "-")[:80]
    extraction = extractor.extract_meeting(transcript, title, date, client_name, our_company)
    memory.retain_meeting(client_name, meeting_id, title, date, extraction)
    return extraction


def load_demo(progress=None):
    """Load the sample Northwind meetings (oldest first)."""
    with open(DEMO_FILE, encoding="utf-8") as f:
        demo = json.load(f)
    meetings = sorted(demo["meetings"], key=lambda m: m["date"])
    for i, m in enumerate(meetings, 1):
        if progress:
            progress(i, len(meetings), m["title"])
        ingest_meeting(demo["client"], demo["our_company"], m["title"], m["date"], m["transcript"], m["id"])
    return demo
