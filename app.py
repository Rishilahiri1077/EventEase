"""
app.py - Streamlit Web-based Chat Interface for EventEase
College Fest Event Registration Agent — EventEase
"""

import os
import streamlit as st
from dotenv import load_dotenv

import tools
from database import init_db, reset_db
from seed import seed_database
from agent import EventEaseAgent, execute_pending_confirmation, get_fest_dates

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="EventEase — College Fest Assistant",
    page_icon="🎪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database if not already created
if not os.path.exists("fest_events.db"):
    seed_database(reset=True)

# Organiser authentication configuration
ORGANISER_PASSWORD = os.getenv("ORGANISER_PASSWORD", "fest2026")


# ============================================================================
# Custom Professional CSS Injection
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2.5rem;
        max-width: 1100px;
    }

    /* Professional Header Hero */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 0.35rem;
        margin-bottom: 0.8rem;
    }
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        background: rgba(255, 255, 255, 0.1);
        color: #e2e8f0;
        border: 1px solid rgba(255, 255, 255, 0.15);
        margin-right: 0.4rem;
    }
    .badge-pill-success {
        background: rgba(16, 185, 129, 0.15);
        color: #6ee7b7;
        border-color: rgba(16, 185, 129, 0.3);
    }

    /* Modern Quick Action Chips */
    .quick-chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 1.25rem;
    }

    /* Chat Messages Polishing */
    .stChatMessage {
        border-radius: 14px !important;
        margin-bottom: 0.85rem !important;
        padding: 0.85rem 1rem !important;
    }

    /* Confirmation Card */
    .confirm-card {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-left: 5px solid #f59e0b;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .confirm-header {
        font-size: 1.05rem;
        font-weight: 700;
        color: #92400e;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .confirm-body {
        font-size: 0.92rem;
        color: #78350f;
        line-height: 1.45;
    }

    /* Event Card in Sidebar */
    .event-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 0.75rem;
        margin-bottom: 0.6rem;
    }
    .category-tech { border-left: 3px solid #3b82f6; }
    .category-cultural { border-left: 3px solid #a855f7; }
    .category-sports { border-left: 3px solid #f97316; }

    /* Footer Branding */
    .sidebar-footer {
        font-size: 0.75rem;
        color: #64748b;
        text-align: center;
        padding-top: 1rem;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Session State Initialisation
# ============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hi! I'm **EventEase**, your official College Fest Event Registration Assistant.\n\n"
                       "I can help you explore schedule details, reserve confirmed seats, obtain tickets, "
                       "manage waitlists, or assist fest organisers with live check-ins and attendee statistics.\n\n"
                       "How may I assist you today?"
        }
    ]

if "pending_confirmation" not in st.session_state:
    st.session_state.pending_confirmation = None

if "session_context" not in st.session_state:
    st.session_state.session_context = {"user_email": "riya@abc.edu"}

if "is_organiser_authenticated" not in st.session_state:
    st.session_state.is_organiser_authenticated = False

if "agent" not in st.session_state:
    st.session_state.agent = EventEaseAgent()

if "input_preset" not in st.session_state:
    st.session_state.input_preset = None


# ============================================================================
# Sidebar Configuration & Controls
# ============================================================================
day1, day2 = get_fest_dates()

with st.sidebar:
    st.markdown("### 🎪 EventEase Hub")
    st.caption("College Fest Operations & Directory")

    # Festival Dates Card
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 0.75rem 0.9rem; margin-bottom: 1.2rem;">
        <div style="font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; font-weight: 700;">Fest Schedule</div>
        <div style="display: flex; justify-content: space-between; margin-top: 0.4rem; font-size: 0.88rem;">
            <span>Day 1 (Today):</span>
            <span style="font-weight: 700; color: #38bdf8;">{day1}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 0.2rem; font-size: 0.88rem;">
            <span>Day 2 (Tomorrow):</span>
            <span style="font-weight: 700; color: #a78bfa;">{day2}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Role Selection & Authentication
    st.markdown("#### 👤 Role & Access")
    role_choice = st.radio(
        "Current Mode:",
        ["Participant", "Organiser"],
        index=1 if st.session_state.is_organiser_authenticated else 0,
        horizontal=True,
        label_visibility="collapsed"
    )

    if role_choice == "Organiser":
        if not st.session_state.is_organiser_authenticated:
            st.info("🔑 Organiser authorization required.")
            entered_pwd = st.text_input("Passcode:", type="password", key="org_pwd_input", placeholder="Enter password (demo: fest2026)")
            if st.button("Unlock Organiser Console", type="primary", use_container_width=True):
                if entered_pwd == ORGANISER_PASSWORD:
                    st.session_state.is_organiser_authenticated = True
                    st.success("Authenticated as Organiser.")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        else:
            st.markdown("""
            <div style="background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); border-radius: 8px; padding: 0.5rem 0.75rem; color: #34d399; font-size: 0.82rem; font-weight: 600; margin-bottom: 0.6rem;">
                🟢 Organiser Access Active
            </div>
            """, unsafe_allow_html=True)
            if st.button("Lock Console", use_container_width=True):
                st.session_state.is_organiser_authenticated = False
                st.rerun()
    else:
        st.session_state.is_organiser_authenticated = False
        st.caption("Mode: Regular Fest Attendee")

    st.markdown("---")

    # 2. Live Event Directory
    with st.expander("📅 Event Directory & Availability", expanded=False):
        cat_filter = st.selectbox("Category:", ["ALL", "TECH", "CULTURAL", "SPORTS"], label_visibility="collapsed")
        avail_only = st.checkbox("Show available seats only", value=False)
        selected_cat = None if cat_filter == "ALL" else cat_filter
        
        ev_data = tools.list_events(category=selected_cat, seats_available=avail_only)
        for ev in ev_data.get("events", []):
            cat_cls = "category-tech" if ev["category"] == "TECH" else ("category-cultural" if ev["category"] == "CULTURAL" else "category-sports")
            st.markdown(f"""
            <div class="event-card {cat_cls}">
                <div style="font-weight: 700; font-size: 0.9rem;">{ev['name']}</div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 2px;">
                    {ev['event_date']} · {ev['start_time']}–{ev['end_time']} · {ev['venue']}
                </div>
                <div style="font-size: 0.78rem; font-weight: 600; color: #38bdf8; margin-top: 4px;">
                    Seats: {ev['available_seats']} / {ev['capacity']} &nbsp;|&nbsp; Fee: INR {ev['fee']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 3. Organiser Live Dashboard (Only when authenticated)
    if st.session_state.is_organiser_authenticated:
        with st.expander("📊 Organiser Live Metrics", expanded=True):
            stats_res = tools.event_stats(is_organiser=True)
            total_events = len(stats_res.get("stats", []))
            total_confirmed = sum(s["confirmed_count"] for s in stats_res.get("stats", []))
            total_waitlisted = sum(s["waitlisted_count"] for s in stats_res.get("stats", []))
            total_checked_in = sum(s["checked_in_count"] for s in stats_res.get("stats", []))

            col_a, col_b = st.columns(2)
            col_a.metric("Confirmed", total_confirmed)
            col_b.metric("Checked-in", total_checked_in)
            
            col_c, col_d = st.columns(2)
            col_c.metric("Waitlisted", total_waitlisted)
            col_d.metric("Events", total_events)

            st.markdown("---")
            longest = tools.event_stats(is_organiser=True, longest_waitlist_only=True)
            st.caption(f"**Highest Waitlist:** {longest.get('message')}")


    # Footer
    st.markdown(f"""
    <div class="sidebar-footer">
        EventEase v2.0 · SQLite Database<br>
        Asia/Kolkata Timezone Enforced
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# Main Content Area
# ============================================================================

# Hero Banner
org_status_pill = (
    '<span class="badge-pill badge-pill-success">🟢 Organiser Console</span>' 
    if st.session_state.is_organiser_authenticated 
    else '<span class="badge-pill">👤 Attendee View</span>'
)

st.markdown(f"""
<div class="hero-banner">
    <div class="hero-title">
        🎪 EventEase
    </div>
    <div class="hero-subtitle">
        Intelligent College Fest Event Registration, Verification, and Operations Assistant
    </div>
    <div>
        {org_status_pill}
        <span class="badge-pill">📅 Day 1: {day1}</span>
        <span class="badge-pill">📅 Day 2: {day2}</span>
        <span class="badge-pill">⚡ Powered by AI</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Suggestion Chips for Fast Interaction
st.markdown("<div style='font-size: 0.8rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 0.4rem;'>Quick Actions</div>", unsafe_allow_html=True)
col_q1, col_q2, col_q3, col_q4 = st.columns(4)

with col_q1:
    if st.button("🔍 Tech Events Tomorrow", use_container_width=True):
        st.session_state.input_preset = "What tech events are happening tomorrow with seats left?"

with col_q2:
    if st.button("📝 Register for Fest", use_container_width=True):
        st.session_state.input_preset = "Register me (riya@abc.edu) for the Hackathon and the Robo Race."

with col_q3:
    if st.button("🎟️ View My Tickets", use_container_width=True):
        st.session_state.input_preset = "Show my registrations for riya@abc.edu"

with col_q4:
    if st.session_state.is_organiser_authenticated:
        if st.button("📊 Longest Waitlist", use_container_width=True):
            st.session_state.input_preset = "(Organiser) Which event has the longest waitlist?"
    else:
        if st.button("❌ Cancel Registration", use_container_width=True):
            st.session_state.input_preset = "Cancel my Robo Race registration."

st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🎪" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

# Prominent Confirmation Card for Data-Changing Actions
if st.session_state.pending_confirmation:
    pending = st.session_state.pending_confirmation
    
    st.markdown(f"""
    <div class="confirm-card">
        <div class="confirm-header">
            ⚠️ Confirmation Required
        </div>
        <div class="confirm-body">
            <strong>Target Action:</strong> {pending.get('summary')}<br>
            Please review and confirm to commit this transaction to the college fest database.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        if st.button("✅ Confirm & Execute Action", type="primary", use_container_width=True):
            res_msg, success = execute_pending_confirmation(
                pending,
                is_organiser=st.session_state.is_organiser_authenticated
            )
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"**Execution Result:**\n\n{res_msg}"
            })
            st.session_state.pending_confirmation = None
            st.rerun()

    with col_c2:
        if st.button("❌ Cancel / Abort", use_container_width=True):
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Action cancelled. No database modifications were made."
            })
            st.session_state.pending_confirmation = None
            st.rerun()


# Determine input prompt (either from preset click or user typing)
incoming_input = None
if st.session_state.input_preset:
    incoming_input = st.session_state.input_preset
    st.session_state.input_preset = None

# Chat input field
chat_input_val = st.chat_input("Ask EventEase (e.g. 'What tech events are happening tomorrow with seats left?')...")
if chat_input_val:
    incoming_input = chat_input_val

if incoming_input:
    # Add user message to conversation history
    st.session_state.messages.append({"role": "user", "content": incoming_input})

    # Process through EventEase Agent
    response_data = st.session_state.agent.process_message(
        user_message=incoming_input,
        session_context=st.session_state.session_context,
        is_organiser=st.session_state.is_organiser_authenticated
    )

    # Update state
    reply_text = response_data.get("reply", "")
    st.session_state.pending_confirmation = response_data.get("pending_confirmation")
    st.session_state.session_context = response_data.get("updated_context", st.session_state.session_context)

    # Append assistant reply
    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    st.rerun()
