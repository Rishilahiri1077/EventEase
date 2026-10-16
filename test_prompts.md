# EventEase — Test Prompts & Verification Report

This document records the verification of the **College Fest Event Registration Agent — EventEase**.
All tests were executed against the live SQLite database populated by [`seed.py`](file:///e:/Incred/seed.py), with timestamps and dates dynamically calculated in the configured timezone (`Asia/Kolkata`).

---

## Environment & Test Context
- **Operating System:** Windows
- **Timezone:** `Asia/Kolkata`
- **Dynamic Fest Dates:**
  - **Day 1 (Today):** `2026-10-16`
  - **Day 2 (Tomorrow):** `2026-10-17`
- **Database File:** `fest_events.db`
- **Test Runner:** [`test_runner.py`](file:///e:/Incred/test_runner.py)

---

## Mandatory Prompt 1: Event Discovery

### Prompt
> **What tech events are happening tomorrow with seats left?**

### Expected Tool Call
```python
list_events(category="TECH", event_date="2026-10-17", seats_available=True)
```

### Expected Database Behaviour
- Query the `events` table joined with active registrations (`status IN ('CONFIRMED', 'CHECKED_IN')`).
- Filter by `category = 'TECH'` and `event_date = '2026-10-17'` (dynamically computed tomorrow's date in `Asia/Kolkata`).
- Filter where `available_seats = capacity - (confirmed_count + checked_in_count) > 0`.
- Return only events meeting all conditions.

### Actual Agent Reply (Captured from Test Run)
```text
Here are the TECH events happening tomorrow (2026-10-17) with seats available:

• **Hackathon** (TECH) — Venue: Innovation Hub | Time: 09:00 - 17:00 | Fee: INR 150.0 | Available Seats: **14** / 20
• **Robotics Workshop** (TECH) — Venue: Mechanical Lab | Time: 10:00 - 13:00 | Fee: INR 100.0 | Available Seats: **15** / 15
• **Web Dev Sprint** (TECH) — Venue: Computer Lab 1 | Time: 14:00 - 16:30 | Fee: INR 0.0 | Available Seats: **5** / 5
```

### Result
- **Status:** **PASSED ✅**
- **Notes:** Full events (such as AI Showcase on Day 2 which is full with waitlist) were correctly excluded from the available seats filter.

---

## Mandatory Prompt 2: Multi-Event Registration & Confirmation

### Prompt
> **Register me (riya@abc.edu) for the Hackathon and the Robo Race.**

### Expected Tool Call
Multi-step confirmation workflow:
1. Summarise the multi-event batch registration and request explicit confirmation.
2. Upon user confirmation, execute:
   ```python
   register_for_event(participant_email_or_id="riya@abc.edu", event_name_or_id="Hackathon")
   register_for_event(participant_email_or_id="riya@abc.edu", event_name_or_id="Robo Race")
   ```

### Expected Database Behaviour
- Identify participant `riya@abc.edu` (Riya Sharma, ID: 1).
- Identify `Hackathon` (Event ID: 7, Day 2: 09:00 - 17:00) and `Robo Race` (Event ID: 1, Day 1: 10:00 - 12:00).
- Check business rules for each event:
  - No duplicate active registrations.
  - Less than 3 confirmed events.
  - No schedule clashes between the two events or with existing registrations.
- Check seat capacity in atomic transactions.
- Insert rows into `registrations` table with unique ticket codes (`FEST-T7-0047` and `FEST-T1-0048`).

### Step 1: Confirmation Request (Captured from Test Run)
```text
I found the requested event(s): **Hackathon and Robo Race** for **riya@abc.edu**.

Please confirm that you want to register for Hackathon and Robo Race. I will check seat availability, the 3-confirmed-event limit, and schedule clashes before processing.
```

### Step 2: Final Result After Confirmation (Captured from Test Run)
```text
Registration Results for riya@abc.edu:

- **Hackathon**: Registration Successful! Riya Sharma is CONFIRMED for 'Hackathon'. Your Ticket Code is: FEST-T7-0047. Venue: Innovation Hub on 2026-10-17 from 09:00 to 17:00.
- **Robo Race**: Registration Successful! Riya Sharma is CONFIRMED for 'Robo Race'. Your Ticket Code is: FEST-T1-0048. Venue: Tech Arena on 2026-10-16 from 10:00 to 12:00.
```

### Result
- **Status:** **PASSED ✅**
- **Notes:** Confirmation workflow succeeded; atomic write operations generated distinct, valid tickets without partial state corruption.

---

## Mandatory Prompt 3: Registration Cancellation & Waitlist Evaluation

### Prompt
> **Cancel my Robo Race registration.**

### Expected Tool Call
1. Summarise the cancellation action and request explicit user confirmation.
2. Upon confirmation, execute:
   ```python
   cancel_registration(participant_email_or_id="riya@abc.edu", event_name_or_id_or_reg_id="Robo Race")
   ```

### Expected Database Behaviour
- Locate registration for participant `riya@abc.edu` in `Robo Race`.
- Verify current status is `CONFIRMED`.
- Begin SQLite transaction:
  - Update `status` to `CANCELLED`.
  - Evaluate waitlist for `Robo Race` (ordered by `registered_at ASC, reg_id ASC`).
  - If an eligible waitlisted participant exists, promote them to `CONFIRMED`. If none are waitlisted, leave seat available.
- Commit transaction.

### Step 1: Confirmation Request (Captured from Test Run)
```text
Please confirm that you want to **CANCEL** your registration for **Robo Race** (Participant: riya@abc.edu). If confirmed, your seat will be freed and any eligible waitlisted participant will be automatically promoted.
```

### Step 2: Final Result After Confirmation (Captured from Test Run)
```text
Registration for 'Robo Race' (Ticket: FEST-T1-0048) has been successfully CANCELLED.
```

### Result
- **Status:** **PASSED ✅**
- **Notes:** Registration was marked `CANCELLED`. In subsequent queries, Riya can re-register or view her cancelled history with status badge.

---

## Mandatory Prompt 4: Organiser Check-In with RBAC Enforcement

### Prompt
> **(Organiser) Check in ticket FEST-T7-0042.**

### Expected Tool Call
1. Validate organiser session authorisation.
2. Summarise check-in action.
3. Upon confirmation, execute:
   ```python
   check_in(ticket_code="FEST-T7-0042", is_organiser=True)
   ```

### Expected Database Behaviour
- If `is_organiser=False`: Immediately reject with access denied.
- If `is_organiser=True`:
  - Locate ticket `FEST-T7-0042` (seeded for participant Vikram Malhotra in Hackathon, initially `CONFIRMED`).
  - Verify status is `CONFIRMED`.
  - Update status to `CHECKED_IN` in SQLite transaction.
  - Return check-in confirmation details (participant name, college, event venue).

### Sub-Test A: Unauthenticated Participant Attempt (RBAC Test)
```text
⛔ **Access Denied**: Check-in is an organiser-only operation. Please switch to the Organiser role and authenticate in the sidebar to proceed.
```

### Sub-Test B: Authenticated Organiser Confirmation Request
```text
Organiser action: Please confirm check-in for ticket **FEST-T7-0042**.
```

### Sub-Test C: Final Result After Organiser Confirmation (Captured from Test Run)
```text
Check-in Successful! Ticket: FEST-T7-0042 | Participant: Vikram Malhotra (XYZ Institute of Tech) | Event: Hackathon at Innovation Hub.
```

### Result
- **Status:** **PASSED ✅**
- **Notes:** RBAC strictly enforced in application code. Seeded ticket `FEST-T7-0042` was checked in once. A subsequent check-in attempt was rejected (Rule E).

---

## Mandatory Prompt 5: Longest Waitlist Analysis (Organiser Only)

### Prompt
> **(Organiser) Which event has the longest waitlist?**

### Expected Tool Call
```python
event_stats(is_organiser=True, longest_waitlist_only=True)
```

### Expected Database Behaviour
- Verify organiser authorization.
- Aggregate live registration counts grouped by `event_id`.
- Sort by `waitlisted_count DESC, event_id ASC` (deterministic tie-breaker).
- Return the event with the highest count of waitlisted participants.

### Sub-Test A: Unauthenticated Participant Attempt
```text
⛔ **Access Denied**: Waitlist rankings and statistics are organiser-only features. Please log in as an organiser to view this data.
```

### Sub-Test B: Authenticated Organiser Reply (Captured from Test Run)
```text
📊 **Waitlist Report:**

The event with the longest waitlist is 'Cricket Tournament' (Event ID: 12) with 5 participant(s) waiting.
```

### Result
- **Status:** **PASSED ✅**
- **Notes:** Correctly identified `Cricket Tournament` with exactly 5 waitlisted participants as defined in seed data.

---

## Business Rule Violation Tests

### Rule A: Time-Clash Prevention
- **Scenario:** Participant Riya Sharma is confirmed for `Robo Race` (`2026-10-16`, 10:00 - 12:00). She then attempts to register for `Coding Challenge` (`2026-10-16`, 11:00 - 13:00).
- **Condition:** Intervals overlap on the same date (`10:00 < 13:00` and `11:00 < 12:00`).
- **Actual Agent / Tool Result:**
  ```text
  Schedule Clash (Rule A): Cannot register for 'Coding Challenge' (2026-10-16 11:00-13:00) because it clashes with your confirmed event 'Robo Race' (10:00-12:00).
  ```
- **Database Consistency:** No registration record was created for `Coding Challenge`. Database remained in a consistent state.
- **Status:** **PASSED ✅**

### Rule B: Maximum Three Confirmed Events
- **Scenario:** Riya Sharma holds 3 confirmed events (`Hackathon`, `Robo Race`, `Dance Battle`). She then attempts to register for a 4th event (`Street Play`).
- **Condition:** Active count (`CONFIRMED` + `CHECKED_IN`) is already 3.
- **Actual Agent / Tool Result:**
  ```text
  Limit Exceeded (Rule B): Riya Sharma already has 3 confirmed events (maximum allowed is 3). Registration rejected.
  ```
- **Database Consistency:** Registration was rejected; waitlisting was not used to bypass the 3-event limit.
- **Status:** **PASSED ✅**

### Rule C: Duplicate Active Registration Prevention
- **Scenario:** Participant attempts to register for `Robo Race` while already holding a confirmed active registration.
- **Actual Agent / Tool Result:**
  ```text
  Duplicate Registration Blocked (Rule C): Riya Sharma is already registered for 'Robo Race' with status CONFIRMED (Ticket: FEST-T1-0048).
  ```
- **Database Consistency:** Enforced by SQLite unique partial index `idx_unique_active_reg` and application validation.
- **Status:** **PASSED ✅**

### Rule D: Automatic Waitlist Promotion on Cancellation
- **Scenario:** `Singing Competition` (Capacity: 5) is full with waitlisted participants. Participant Neha Kakkar cancels her confirmed registration (`FEST-T10-0013`).
- **Actual Agent / Tool Result:**
  ```text
  Registration for 'Singing Competition' (Ticket: FEST-T10-0013) has been successfully CANCELLED. Automatic waitlist promotion (Rule D): Waitlisted participant 'Fatima Sana' has been promoted to CONFIRMED (Ticket: FEST-T10-0018).
  ```
- **Database Consistency:** In a single atomic SQLite transaction, the cancelling participant was marked `CANCELLED` and earliest eligible waitlisted candidate (`Fatima Sana`) was promoted to `CONFIRMED`, retaining her ticket code.
- **Status:** **PASSED ✅**

### Rule E: One-Time Check-In Enforcement
- **Scenario:** Organiser attempts to check in ticket `FEST-T7-0042` a second time after it was already checked in.
- **Actual Agent / Tool Result:**
  ```text
  Check-In Rejected (Rule E): Ticket 'FEST-T7-0042' for Vikram Malhotra has ALREADY been checked in. Duplicate check-ins are not permitted.
  ```
- **Database Consistency:** Duplicate check-in was blocked; registration remained `CHECKED_IN` without duplicate entries or errors.
- **Status:** **PASSED ✅**

---

## Summary of Test Results

| Test # | Test Description | Tool Invoked | Expected vs Actual | Result |
|---|---|---|---|---|
| **1** | Discover tech events tomorrow with seats | `list_events` | Matches dynamic date & available seats | **PASSED ✅** |
| **2** | Register for Hackathon & Robo Race | `register_for_event` | Two-step confirmation & unique tickets | **PASSED ✅** |
| **3** | Cancel Robo Race registration | `cancel_registration` | Frees seat, checks waitlist | **PASSED ✅** |
| **4** | Check in ticket FEST-T7-0042 | `check_in` | RBAC blocks unauth; organiser checks in | **PASSED ✅** |
| **5** | Event with longest waitlist | `event_stats` | Identified Cricket Tournament (5 waiting) | **PASSED ✅** |
| **BR-A**| Time clash schedule overlap | `register_for_event` | Blocked overlapping times on same day | **PASSED ✅** |
| **BR-B**| Max 3 confirmed events limit | `register_for_event` | Blocked 4th event attempt | **PASSED ✅** |
| **BR-C**| Duplicate active registration | `register_for_event` | Blocked duplicate registration | **PASSED ✅** |
| **BR-D**| Auto waitlist promotion | `cancel_registration` | Earliest eligible candidate promoted | **PASSED ✅** |
| **BR-E**| One-time check-in | `check_in` | Blocked duplicate check-in attempt | **PASSED ✅** |
