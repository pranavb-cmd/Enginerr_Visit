# app.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os
from streamlit_calendar import calendar

# File to store visits
DATA_FILE = "visits.json"

def load_visits():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_visits(visits):
    with open(DATA_FILE, 'w') as f:
        json.dump(visits, f, indent=2)

# ── Load data into session state ──
if 'visits' not in st.session_state:
    st.session_state.visits = load_visits()

# ── Page config ──
st.set_page_config(page_title="Engineer Visit Scheduler", layout="wide")

st.title("🛠️ Engineer Visit Scheduler")
st.markdown("Schedule visits and view them on a calendar.")

# ── Sidebar filters ──
st.sidebar.header("Filters")
show_all = st.sidebar.checkbox("Show past & cancelled visits", value=False)
engineer_filter = st.sidebar.text_input("Filter by engineer name")

# ── Add new visit form (with clear after submit) ──
with st.expander("➕ Schedule New Visit", expanded=True):
    with st.form(key="new_visit_form", clear_on_submit=True):  # This helps with clearing
        customer = st.text_input("Customer / Company")
        phone = st.text_input("Phone Number")
        address = st.text_area("Address / Location")
        col1, col2 = st.columns(2)
        visit_date = col1.date_input("Visit Date", min_value=date.today(), key="visit_date")
        visit_time = col2.time_input("Preferred Time", key="visit_time")
        engineer = st.text_input("Engineer Name", value="TBD")
        notes = st.text_area("Notes / Problem Description")
        
        submitted = st.form_submit_button("Schedule Visit")
        
        if submitted:
            if not customer.strip():
                st.error("Customer name is required!")
            else:
                new_visit = {
                    "customer": customer.strip(),
                    "phone": phone.strip(),
                    "address": address.strip(),
                    "date": str(visit_date),
                    "time": str(visit_time)[:5],
                    "engineer": engineer.strip() or "TBD",
                    "notes": notes.strip(),
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "status": "scheduled"
                }
                st.session_state.visits.append(new_visit)
                save_visits(st.session_state.visits)
                st.success("Visit scheduled successfully!")
                st.rerun()

# ── Calendar View ──
st.header("Calendar View")

# Prepare events for calendar (FullCalendar format)
events = []
filtered_visits = st.session_state.visits

if not show_all:
    today = date.today()
    filtered_visits = [v for v in filtered_visits if v["status"] == "scheduled" and datetime.fromisoformat(v["date"]).date() >= today]

if engineer_filter:
    filtered_visits = [v for v in filtered_visits if engineer_filter.lower() in v["engineer"].lower()]

for v in filtered_visits:
    start_datetime = f"{v['date']}T{v['time']}:00"
    events.append({
        "id": str(len(events)),  # simple unique id
        "title": f"{v['engineer']} - {v['customer']}",
        "start": start_datetime,
        "extendedProps": {
            "customer": v["customer"],
            "phone": v["phone"],
            "address": v["address"],
            "time": v["time"],
            "notes": v["notes"],
            "status": v["status"]
        },
        "backgroundColor": "#3788d8" if v["status"] == "scheduled" else "#dc3545"
    })

# Calendar options (month view by default)
calendar_options = {
    "editable": False,
    "selectable": False,
    "initialView": "dayGridMonth",
    "headerToolbar": {
        "left": "prev,next today",
        "center": "title",
        "right": "dayGridMonth,dayGridWeek,dayGridDay"
    },
    "height": 650,
}

# Custom event content (shows more info on hover/click)
custom_css = """
    .fc-event-title {
        white-space: normal;
    }
"""

calendar(
    events=events,
    options=calendar_options,
    callbacks=["eventClick", "dateClick"],
    custom_css=custom_css
)

# Show details when user clicks an event
if "eventClick" in st.session_state:
    event = st.session_state.eventClick.get("event", {})
    if event:
        props = event.get("extendedProps", {})
        st.info(f"**Selected Visit:**\n\n"
                f"**Engineer:** {event.get('title', '').split(' - ')[0]}\n"
                f"**Customer:** {props.get('customer', 'N/A')}\n"
                f"**Time:** {props.get('time', 'N/A')}\n"
                f"**Phone:** {props.get('phone', 'N/A')}\n"
                f"**Address:** {props.get('address', 'N/A')}\n"
                f"**Notes:** {props.get('notes', 'N/A')}\n"
                f"**Status:** {props.get('status', 'N/A')}")

# Optional: fallback table if needed
with st.expander("List View (detailed table)"):
    if filtered_visits:
        df = pd.DataFrame(filtered_visits)
        df = df.sort_values("date")
        st.dataframe(
            df[["date", "time", "customer", "engineer", "phone", "status", "notes"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No visits match the current filters.")

st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}")
