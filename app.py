# app.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os

# File to store visits (persists on disk in Streamlit Cloud)
DATA_FILE = "visits.json"

def load_visits():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_visits(visits):
    with open(DATA_FILE, 'w') as f:
        json.dump(visits, f, indent=2)

# Load existing data
if 'visits' not in st.session_state:
    st.session_state.visits = load_visits()

# ────────────────────────────────────────────────
st.title("🛠️ Engineer Visit Scheduler")
st.markdown("Schedule and manage engineer visits easily.")

# ── Sidebar filters ──
st.sidebar.header("Filters")
show_all = st.sidebar.checkbox("Show all visits (including past/cancelled)", value=False)
engineer_filter = st.sidebar.text_input("Filter by engineer name")

# ── Add new visit form ──
with st.expander("➕ Schedule New Visit", expanded=True):
    with st.form("new_visit"):
        customer = st.text_input("Customer / Company", key="cust")
        phone = st.text_input("Phone Number")
        address = st.text_area("Address / Location")
        col1, col2 = st.columns(2)
        visit_date = col1.date_input("Visit Date", min_value=date.today())
        visit_time = col2.time_input("Preferred Time")
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
                    "time": str(visit_time)[:5],  # HH:MM
                    "engineer": engineer.strip() or "TBD",
                    "notes": notes.strip(),
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "status": "scheduled"
                }
                st.session_state.visits.append(new_visit)
                save_visits(st.session_state.visits)
                st.success("Visit scheduled!")
                st.rerun()   # refresh page

# ── Display visits ──
st.header("Scheduled Visits")

df = pd.DataFrame(st.session_state.visits)

if not df.empty:
    # Filter logic
    today = date.today()
    df['visit_date'] = pd.to_datetime(df['date']).dt.date
    
    if not show_all:
        df = df[df['status'] == 'scheduled']
        df = df[df['visit_date'] >= today]
    
    if engineer_filter:
        df = df[df['engineer'].str.contains(engineer_filter, case=False, na=False)]
    
    df = df.sort_values("date")
    
    # Nice columns
    display_cols = ["date", "time", "customer", "engineer", "phone", "status"]
    st.dataframe(
        df[display_cols + (["notes"] if "notes" in df else [])],
        column_config={
            "date": "Date",
            "time": "Time",
            "customer": "Customer",
            "engineer": "Engineer",
            "phone": "Phone",
            "status": "Status",
            "notes": "Notes"
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Cancel option
    st.subheader("Cancel a Visit")
    cancel_idx = st.number_input("Enter row number to cancel (0-based index from table above)", min_value=0, max_value=len(df)-1 if not df.empty else 0, step=1)
    
    if st.button("Cancel Selected Visit"):
        if 0 <= cancel_idx < len(st.session_state.visits):
            orig_idx = st.session_state.visits.index(df.iloc[cancel_idx].to_dict())
            st.session_state.visits[orig_idx]["status"] = "cancelled"
            save_visits(st.session_state.visits)
            st.success("Visit cancelled.")
            st.rerun()
        else:
            st.error("Invalid row number.")
else:
    st.info("No visits scheduled yet. Add one above!")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
