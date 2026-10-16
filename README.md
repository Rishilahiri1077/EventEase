

## 1. Project Description & Objectives

EventEase is a beginner-friendly, AI-powered conversational registration assistant designed for a college fest. It serves two distinct user personas:
1.Fest Participants:Discover events across categories (Tech, Cultural, Sports), register for events, receive deterministic ticket codes, join waitlists when events reach capacity, cancel registrations with automatic waitlist promotions, and view all active and historical tickets.
2.Fest Organisers: Authorised operations including checking in attendees using ticket codes, inspecting aggregate registration counts, and identifying events with the longest waitlist.

EventEase is built on a real SQLite database. Every business rule (time clashes, 3-event limit, duplicate prevention, waitlist promotion, one-time check-in) is enforced directly in Python database functions and transactional SQL, rather than relying solely on AI prompts.

---

## 2. Technology Stack

Programming Language: Python 3.11+
Database: SQLite3 with foreign key enforcement and transactional integrity
Web UI & Chat Interface:[Streamlit](https://streamlit.io/)
LLM SDK & Tool Calling: [Groq Python SDK](https://github.com/groq/groq-python) (`groq`) using high-speed models (e.g. `llama-3.3-70b-versatile`)
Environment Management: `python-dotenv`
Date & Timezone Validation: Python `datetime` and `zoneinfo` (`Asia/Kolkata` timezone)
Unique Ticket Identifiers: Deterministic ticket formatting (`FEST-T{event_id}-{reg_id:04d}`)



## 4. Required Project Structure

```text
Incred/
├── app.py              # Streamlit chat interface and session memory
├── agent.py            # EventEase persona, Groq tool selection, and response generator
├── tools.py            # All 7 database-backed tools and business rules
├── database.py         # SQLite connection, transaction helpers, and initialization
├── schema.sql          # Database tables, constraints, foreign keys, and indexes
├── seed.py             # Reproducible seed data generator (14 events, 32 participants, 46 registrations)
├── test_runner.py      # Automated test runner for prompts and business rules
├── test_prompts.md     # Detailed test logs for the 5 mandatory prompts and rule tests
├── requirements.txt    # Python package dependencies
├── .env.example        # Environment variable template
├── .gitignore          # Git exclusion rules for secrets, DB, and virtual environments
└── README.md           # Setup, architecture, and user guide
```

---

## 5. Prerequisites
Python 3.11 or newer installed.
Git (optional, for version control).
A Groq API Key from [Groq Console (console.groq.com)](https://console.groq.com/keys) (optional for AI conversational mode; offline Command Mode works out-of-the-box without an API key).

---

## 6. Installation & Setup

### Windows (PowerShell)

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate the virtual environment
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file from template
Copy-Item .env.example .env

# 5. Initialise and seed the SQLite database
python seed.py

# 6. Run the Streamlit web application
streamlit run app.py
```

### macOS / Linux

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file from template
cp .env.example .env

# 5. Initialise and seed the SQLite database
python seed.py

# 6. Run the Streamlit web application
streamlit run app.py
```

---

## 7. Configuration (.env)

Edit the generated `.env` file to configure your application:

```ini
# Groq API Key (leave empty for offline Command Mode)
GROQ_API_KEY=your_groq_api_key_here

# Groq Model identifier
GROQ_MODEL=llama-3.3-70b-versatile

# Demo Organiser Password for check-in and statistics access
ORGANISER_PASSWORD=fest2026

# SQLite database file path
DATABASE_PATH=fest_events.db
```

---

## 8. The Seven Implemented Tools

All seven tools are defined in [`tools.py`](file:///e:/Incred/tools.py) as plain Python functions that read and write directly to SQLite:

| Tool Name | Parameters | Purpose & Description |
|---|---|---|
| **1. `list_events`** | `category`, `event_date`, `seats_available` | Lists and filters fest events. Computes live available seats (`capacity - confirmed - checked_in`) and waitlist count. |
| **2. `register_participant`** | `name`, `email`, `college`, `phone` | Registers a new participant profile. If email already exists, retrieves existing record without overwriting. |
| **3. `register_for_event`** | `participant_email_or_id`, `event_name_or_id` | Registers a participant for an event in an atomic transaction. Enforces Rules A, B, and C. Issues `CONFIRMED` or `WAITLISTED` ticket. |
| **4. `cancel_registration`** | `participant_email_or_id`, `event_name_or_id_or_reg_id` | Cancels an active registration. If it was `CONFIRMED`, triggers Rule D (automatic waitlist promotion) in the same transaction. |
| **5. `get_my_registrations`** | `participant_email_or_id` | Retrieves all active, waitlisted, checked-in, and cancelled registrations for a participant. |
| **6. `check_in`** | `ticket_code`, `is_organiser` | Checks in an attendee with a `CONFIRMED` ticket. Enforces Rule E and role authorization in application code. |
| **7. `event_stats`** | `is_organiser`, `longest_waitlist_only` | Provides organisers with capacity, confirmed, waitlist, and seat metrics. Supports deterministic ranking of longest waitlist. |

---

## 9. Business Rules (Enforced in Code)

1. **Rule A (Time-Clash Prevention):**
   - A participant cannot hold two confirmed registrations for events whose schedules overlap on the same date.
   - Overlap condition: `A.start_time < B.end_time AND B.start_time < A.end_time`.
   - Adjacent events (where one event ends exactly when the other begins) are allowed.
2. **Rule B (Maximum 3 Confirmed Events):**
   - A participant can hold at most 3 registrations with status `CONFIRMED` or `CHECKED_IN`.
   - Attempting a 4th registration is rejected (it is not placed on the waitlist to bypass the limit).
3. **Rule C (No Duplicate Active Registrations):**
   - A participant cannot register for the same event more than once while an active registration (`CONFIRMED`, `WAITLISTED`, `CHECKED_IN`) exists.
   - Enforced by both Python logic and SQLite partial unique index:
     `CREATE UNIQUE INDEX idx_unique_active_reg ON registrations(participant_id, event_id) WHERE status != 'CANCELLED';`
4. **Rule D (Automatic Waitlist Promotion):**
   - When a `CONFIRMED` participant cancels, the seat is automatically offered to the earliest registered waitlisted participant (`registered_at ASC, reg_id ASC`).
   - The candidate is evaluated for the 3-event limit and time clashes; if ineligible, they remain waitlisted and the next candidate is evaluated.
   - Promotion happens in the same atomic transaction; the participant's original ticket code is preserved.
5. **Rule E (One-Time Check-In):**
   - Only tickets with `CONFIRMED` status may be checked in.
   - Only authenticated organisers can check in tickets.
   - A ticket cannot be checked in more than once. `WAITLISTED` or `CANCELLED` tickets are rejected.

---

## 10. Confirmation & Safety Workflow

Before any data-changing write operation (event registration, multi-event batch registration, cancellation, or organiser check-in), EventEase:
1. Summarises the proposed action in the chat.
2. Displays interactive **Confirm Action** and **Cancel Action** buttons in the Streamlit UI.
3. Does **not** execute any database mutation until the user clicks **Confirm**.
4. In multi-event registrations, each event is evaluated independently: if one fails due to a time clash, the other may succeed, and the status of both is accurately reported.

---

## 11. Role-Based Access Control (RBAC)

- The application provides a **Role Selector** in the sidebar ("Participant" vs "Organiser").
- Simply selecting "Organiser" does **not** grant organiser privileges.
- An organiser must authenticate using the password configured in `ORGANISER_PASSWORD` (`fest2026`).
- Organiser-only tools (`check_in`, `event_stats`) verify `is_organiser=True` inside Python functions before executing any database operation.

---

## 12. Sample Workflows

### Participant Workflow
1. **Search Events:**
   - Type: *"What tech events are happening tomorrow with seats left?"*
   - EventEase lists all tech events on tomorrow's fest date with remaining seats.
2. **Batch Registration:**
   - Type: *"Register me (riya@abc.edu) for the Hackathon and the Robo Race."*
   - EventEase summarises the events and asks for confirmation.
   - Click **Confirm Action**. EventEase issues tickets `FEST-T7-0047` and `FEST-T1-0048`.
3. **Cancel a Registration:**
   - Type: *"Cancel my Robo Race registration."*
   - Click **Confirm Action**. The registration is cancelled and the seat is freed.
4. **Check My Tickets:**
   - Type: *"Show my registrations for riya@abc.edu."*
   - EventEase displays a summary table with ticket codes and statuses.

### Organiser Workflow
1. **Log In:** Switch role to "Organiser" in the sidebar and enter password `fest2026`.
2. **Check In an Attendee:**
   - Type: *"Check in ticket FEST-T7-0042."*
   - Click **Confirm Action**. Ticket status updates to `CHECKED_IN`.
3. **Inspect Longest Waitlist:**
   - Type: *"Which event has the longest waitlist?"*
   - EventEase reports `Cricket Tournament` with 5 waitlisted participants.

---

## 13. Running Automated Tests

To run the automated test suite covering all 5 mandatory prompts and all 5 business rule violation tests:

```bash
python test_runner.py
```

Expected output:
```text

Starting EventEase Automated Test Suite

...

OVERALL TEST SUITE: ALL TESTS PASSED 

```

Detailed test logs and outputs are documented in [`test_prompts.md`](file:///e:/Incred/test_prompts.md).

---

## 14. Troubleshooting

- **Database out of sync:** Run `python seed.py` or click **Reset & Reseed Database** in the Streamlit sidebar to reinitialise clean demo data.
- **Groq API quota exceeded or no API key:** The application automatically runs in Command Mode, giving you full access to all database features. You can also paste your Groq API key in the sidebar at runtime.
- **Port already in use:** Run `streamlit run app.py --server.port 8502`.
- **Foreign keys in SQLite:** SQLite foreign key enforcement is automatically enabled on every connection via `PRAGMA foreign_keys = ON;`.
