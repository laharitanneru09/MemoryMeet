"""MemoryMeet UI. Run with:  streamlit run app.py"""
from datetime import date

import streamlit as st

import analyzer
import config
import memory
import pipeline

st.set_page_config(page_title="MemoryMeet", page_icon="🧠", layout="wide")
st.title("MemoryMeet")
st.caption("Don't just remember what was said. Know what changed.")

# ---------- Sidebar: settings ----------
with st.sidebar:
    st.header("Workspace")
    client_name = st.text_input("Client", value="Northwind Logistics")
    our_company = st.text_input("Your company", value="RouteIQ")

    missing = config.missing_config()
    if missing:
        st.error("Missing in .env: " + ", ".join(missing))
        st.stop()

    st.divider()
    st.write("First time? Load 5 sample meetings into memory.")
    if st.button("Load demo data"):
        bar = st.progress(0.0, text="Starting...")
        try:
            pipeline.load_demo(
                progress=lambda i, n, t: bar.progress(i / n, text=f"Ingesting {i}/{n}: {t}")
            )
            bar.progress(1.0, text="Done")
            st.success("Demo data stored in Hindsight.")
        except Exception as e:
            st.error(f"Could not load demo data: {e}")

tab_add, tab_brief, tab_ask = st.tabs(
    ["1. Add meeting", "2. Prep briefing", "3. Ask memory"]
)

# ---------- Tab 1: write path ----------
with tab_add:
    st.subheader("Add a meeting transcript")
    c1, c2 = st.columns(2)
    title = c1.text_input("Meeting title", placeholder="Roadmap review")
    when = c2.date_input("Meeting date", value=date.today())
    uploaded = st.file_uploader("Upload transcript (.txt)", type=["txt"])
    text = st.text_area("...or paste transcript", height=200)
    transcript = uploaded.read().decode("utf-8") if uploaded else text

    if st.button("Extract and save to memory", type="primary"):
        if not title or not transcript.strip():
            st.warning("Add a title and a transcript first.")
        else:
            with st.spinner("Extracting facts and storing in Hindsight..."):
                try:
                    ex = pipeline.ingest_meeting(
                        client_name, our_company, title, when.isoformat(), transcript
                    )
                    st.success("Saved to memory.")
                    st.json(ex)
                except Exception as e:
                    st.error(f"Something failed: {e}")

# ---------- Tab 2: read path ----------
with tab_brief:
    st.subheader("Prep for an upcoming meeting")
    c1, c2 = st.columns(2)
    up_title = c1.text_input("Upcoming meeting", value="Q3 business review")
    up_date = c2.date_input("Date", value=date.today(), key="up_date")
    attendees = st.text_input("Attendees", value="Priya Nair (VP Ops), Daniel Reyes (IT Director)")
    agenda = st.text_area("Agenda", value="Review progress, roadmap, and renewal pricing.", height=80)
    compare = st.checkbox("Also show the 'without memory' briefing", value=True)

    if st.button("Generate briefing", type="primary"):
        upcoming = {
            "title": up_title, "date": up_date.isoformat(),
            "attendees": attendees, "agenda": agenda,
        }
        try:
            with st.spinner("Recalling history from Hindsight..."):
                memories = analyzer.gather_history(client_name)
            if not memories:
                st.warning("No memories found. Load demo data or add a meeting first.")
                st.stop()
            with st.spinner("Detecting what changed..."):
                changes = analyzer.detect_changes(memories, upcoming)
            with st.spinner("Writing briefing..."):
                briefing = analyzer.generate_briefing(changes, memories, upcoming)
                baseline = analyzer.generic_briefing(upcoming) if compare else None

            st.session_state["result"] = (changes, briefing, baseline, memories)
        except Exception as e:
            st.error(f"Something failed: {e}")

    if "result" in st.session_state:
        changes, briefing, baseline, memories = st.session_state["result"]
        icon = {"high": "🔴", "medium": "🟠", "low": "🟡"}
        st.markdown("### What changed")
        if not changes:
            st.info("No meaningful changes detected.")
        for c in changes:
            label = f"{icon.get(c.get('severity'), '⚪')} {c.get('title')}  ·  {c.get('type')}"
            with st.expander(label):
                st.write(c.get("what_changed"))
                st.write("**Affected:** " + str(c.get("affected", "")))
                for ev in c.get("evidence", []):
                    st.caption(ev)

        st.markdown("### Briefing")
        if baseline:
            left, right = st.columns(2)
            left.markdown("**Without memory**")
            left.markdown(baseline)
            right.markdown("**With MemoryMeet (Hindsight)**")
            right.markdown(briefing)
        else:
            st.markdown(briefing)

        with st.expander(f"Raw memories recalled from Hindsight ({len(memories)})"):
            for m in memories:
                st.caption(f"[{m['type']}] {m['text']}")

# ---------- Tab 3: reflect ----------
with tab_ask:
    st.subheader("Ask the memory anything")
    q = st.text_input("Question", value="What does the client expect from us that we may not deliver?")
    if st.button("Ask"):
        try:
            with st.spinner("Reflecting over memory..."):
                st.markdown(memory.ask_memory(client_name, q))
        except Exception as e:
            st.error(f"Something failed: {e}")
