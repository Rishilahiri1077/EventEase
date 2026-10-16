"""
tools.py - Database-Backed Tools and Business Rules for EventEase
College Fest Event Registration Agent — EventEase
"""

import os
import re
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from zoneinfo import ZoneInfo

from database import get_db_connection

# Configured fest timezone
KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


def get_current_date() -> date:
    """Return the current date in Asia/Kolkata timezone."""
    return datetime.now(KOLKATA_TZ).date()


def get_tomorrow_date() -> date:
    """Return tomorrow's date in Asia/Kolkata timezone."""
    return get_current_date() + timedelta(days=1)


def normalise_email(email: str) -> str:
    """Trim whitespace and convert email address to lowercase."""
    return email.strip().lower() if email else ""


def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


# ============================================================================
# TOOL 1: list_events
# ============================================================================
def list_events(
    category: Optional[str] = None,
    event_date: Optional[str] = None,
    seats_available: bool = False
) -> Dict[str, Any]:
    """
    List and filter college fest events.
    
    Args:
        category: Filter by TECH, CULTURAL, or SPORTS (case-insensitive)
        event_date: Filter by date (YYYY-MM-DD)
        seats_available: If True, return only events with remaining seats
    """
    conn = get_db_connection()
    try:
        # Validate category if provided
        cat_upper = category.upper() if category else None
        if cat_upper and cat_upper not in ("TECH", "CULTURAL", "SPORTS"):
            return {
                "success": False,
                "message": f"Invalid category '{category}'. Allowed categories are TECH, CULTURAL, or SPORTS.",
                "events": []
            }
            
        # Validate date if provided
        if event_date:
            try:
                datetime.strptime(event_date.strip(), "%Y-%m-%d")
                event_date = event_date.strip()
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid date format '{event_date}'. Please use YYYY-MM-DD.",
                    "events": []
                }

        # Build parameterised SQL query with live registration counts
        query = """
            SELECT 
                e.event_id,
                e.name,
                e.category,
                e.venue,
                e.event_date,
                e.start_time,
                e.end_time,
                e.capacity,
                e.fee,
                COALESCE(SUM(CASE WHEN r.status = 'CONFIRMED' THEN 1 ELSE 0 END), 0) AS confirmed_count,
                COALESCE(SUM(CASE WHEN r.status = 'CHECKED_IN' THEN 1 ELSE 0 END), 0) AS checked_in_count,
                COALESCE(SUM(CASE WHEN r.status = 'WAITLISTED' THEN 1 ELSE 0 END), 0) AS waitlisted_count
            FROM events e
            LEFT JOIN registrations r ON e.event_id = r.event_id
            WHERE 1=1
        """
        params = []

        if cat_upper:
            query += " AND e.category = ?"
            params.append(cat_upper)

        if event_date:
            query += " AND e.event_date = ?"
            params.append(event_date)

        query += " GROUP BY e.event_id ORDER BY e.event_date, e.start_time, e.name"

        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        events_list = []
        for row in rows:
            active_confirmed = row["confirmed_count"] + row["checked_in_count"]
            available = max(0, row["capacity"] - active_confirmed)

            if seats_available and available <= 0:
                continue

            events_list.append({
                "event_id": row["event_id"],
                "name": row["name"],
                "category": row["category"],
                "venue": row["venue"],
                "event_date": row["event_date"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "fee": float(row["fee"]),
                "capacity": row["capacity"],
                "confirmed_count": row["confirmed_count"],
                "checked_in_count": row["checked_in_count"],
                "waitlisted_count": row["waitlisted_count"],
                "available_seats": available
            })

        if not events_list:
            filter_desc = []
            if cat_upper:
                filter_desc.append(f"category='{cat_upper}'")
            if event_date:
                filter_desc.append(f"date='{event_date}'")
            if seats_available:
                filter_desc.append("with available seats")
            filters_str = " (" + ", ".join(filter_desc) + ")" if filter_desc else ""
            return {
                "success": True,
                "count": 0,
                "message": f"No events found matching your criteria{filters_str}.",
                "events": []
            }

        return {
            "success": True,
            "count": len(events_list),
            "message": f"Found {len(events_list)} event(s).",
            "events": events_list
        }
    finally:
        conn.close()


# ============================================================================
# TOOL 2: register_participant
# ============================================================================
def register_participant(
    name: str,
    email: str,
    college: str,
    phone: str
) -> Dict[str, Any]:
    """
    Find or create a participant profile in the database.
    If the email already exists, returns the existing participant without overwriting.
    """
    # Validate required fields
    missing_fields = []
    if not name or not name.strip():
        missing_fields.append("name")
    if not email or not email.strip():
        missing_fields.append("email")
    if not college or not college.strip():
        missing_fields.append("college")
    if not phone or not phone.strip():
        missing_fields.append("phone")

    if missing_fields:
        return {
            "success": False,
            "message": f"Missing required participant details: {', '.join(missing_fields)}. Please provide all fields."
        }

    norm_email = normalise_email(email)
    if not is_valid_email(norm_email):
        return {
            "success": False,
            "message": f"Invalid email format: '{email}'. Please provide a valid email address."
        }

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Check if participant already exists
        cursor.execute("SELECT * FROM participants WHERE email = ?", (norm_email,))
        existing = cursor.fetchone()
        if existing:
            return {
                "success": True,
                "already_exists": True,
                "message": f"Participant with email '{norm_email}' already exists.",
                "participant": {
                    "participant_id": existing["participant_id"],
                    "name": existing["name"],
                    "email": existing["email"],
                    "college": existing["college"],
                    "phone": existing["phone"]
                }
            }

        # Insert new participant
        cursor.execute(
            """
            INSERT INTO participants (name, email, college, phone)
            VALUES (?, ?, ?, ?)
            """,
            (name.strip(), norm_email, college.strip(), phone.strip())
        )
        conn.commit()
        new_id = cursor.lastrowid

        return {
            "success": True,
            "already_exists": False,
            "message": f"Successfully registered participant '{name.strip()}' with email '{norm_email}'.",
            "participant": {
                "participant_id": new_id,
                "name": name.strip(),
                "email": norm_email,
                "college": college.strip(),
                "phone": phone.strip()
            }
        }
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Database integrity error registering participant: {str(e)}"
        }
    finally:
        conn.close()


# ============================================================================
# TOOL 3: register_for_event
# ============================================================================
def register_for_event(
    participant_email_or_id: str,
    event_name_or_id: str
) -> Dict[str, Any]:
    """
    Register a participant for one event, enforcing:
    - Rule C: No duplicate active registrations
    - Rule B: Max 3 confirmed events
    - Rule A: Time clash prevention
    - Available seats check -> CONFIRMED or WAITLISTED
    - Atomic transaction with unique ticket code generation
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")

        # 1. Resolve participant
        participant = None
        if str(participant_email_or_id).isdigit():
            cursor.execute("SELECT * FROM participants WHERE participant_id = ?", (int(participant_email_or_id),))
            participant = cursor.fetchone()
        if not participant:
            norm_email = normalise_email(str(participant_email_or_id))
            cursor.execute("SELECT * FROM participants WHERE email = ?", (norm_email,))
            participant = cursor.fetchone()

        if not participant:
            conn.rollback()
            return {
                "success": False,
                "message": f"Participant '{participant_email_or_id}' was not found. Please register as a participant first."
            }

        participant_id = participant["participant_id"]
        participant_name = participant["name"]

        # 2. Resolve event
        event = None
        if str(event_name_or_id).isdigit():
            cursor.execute("SELECT * FROM events WHERE event_id = ?", (int(event_name_or_id),))
            event = cursor.fetchone()
        if not event:
            search_name = str(event_name_or_id).strip()
            cursor.execute("SELECT * FROM events WHERE LOWER(name) = LOWER(?)", (search_name,))
            event = cursor.fetchone()
            if not event:
                # Try prefix/substring match if exact didn't hit
                cursor.execute("SELECT * FROM events WHERE LOWER(name) LIKE LOWER(?)", (f"%{search_name}%",))
                event = cursor.fetchone()

        if not event:
            conn.rollback()
            return {
                "success": False,
                "message": f"Event '{event_name_or_id}' was not found. Please check event listings."
            }

        event_id = event["event_id"]
        event_name = event["name"]
        event_date = event["event_date"]
        start_time = event["start_time"]
        end_time = event["end_time"]
        capacity = event["capacity"]

        # 3. Rule C: Check for duplicate active registration
        cursor.execute(
            """
            SELECT * FROM registrations 
            WHERE participant_id = ? AND event_id = ? AND status != 'CANCELLED'
            """,
            (participant_id, event_id)
        )
        existing_active = cursor.fetchone()
        if existing_active:
            conn.rollback()
            return {
                "success": False,
                "message": (
                    f"Duplicate Registration Blocked (Rule C): {participant_name} is already registered "
                    f"for '{event_name}' with status {existing_active['status']} "
                    f"(Ticket: {existing_active['ticket_code']})."
                )
            }

        # 4. Rule B: Check maximum 3 confirmed events
        cursor.execute(
            """
            SELECT COUNT(*) AS active_count 
            FROM registrations 
            WHERE participant_id = ? AND status IN ('CONFIRMED', 'CHECKED_IN')
            """,
            (participant_id,)
        )
        row = cursor.fetchone()
        active_count = row["active_count"] if row else 0

        if active_count >= 3:
            conn.rollback()
            return {
                "success": False,
                "message": (
                    f"Limit Exceeded (Rule B): {participant_name} already has {active_count} confirmed events "
                    f"(maximum allowed is 3). Registration rejected."
                )
            }

        # 5. Rule A: Check time-clash against existing CONFIRMED or CHECKED_IN events
        # Overlap condition: target_start < existing_end AND existing_start < target_end on same event_date
        cursor.execute(
            """
            SELECT e.name, e.event_date, e.start_time, e.end_time 
            FROM registrations r
            JOIN events e ON r.event_id = e.event_id
            WHERE r.participant_id = ? 
              AND r.status IN ('CONFIRMED', 'CHECKED_IN')
              AND e.event_date = ?
            """,
            (participant_id, event_date)
        )
        existing_events = cursor.fetchall()
        for ex in existing_events:
            ex_name = ex["name"]
            ex_start = ex["start_time"]
            ex_end = ex["end_time"]
            # Overlap formula: A.start < B.end AND B.start < A.end
            if start_time < ex_end and ex_start < end_time:
                conn.rollback()
                return {
                    "success": False,
                    "message": (
                        f"Schedule Clash (Rule A): Cannot register for '{event_name}' "
                        f"({event_date} {start_time}-{end_time}) because it clashes with your confirmed "
                        f"event '{ex_name}' ({ex_start}-{ex_end})."
                    )
                }

        # 6. Check capacity to determine CONFIRMED vs WAITLISTED
        cursor.execute(
            """
            SELECT COUNT(*) AS occupied 
            FROM registrations 
            WHERE event_id = ? AND status IN ('CONFIRMED', 'CHECKED_IN')
            """,
            (event_id,)
        )
        occ_row = cursor.fetchone()
        occupied = occ_row["occupied"] if occ_row else 0
        available = capacity - occupied

        now_str = datetime.now(KOLKATA_TZ).strftime("%Y-%m-%dT%H:%M:%S")

        if available > 0:
            reg_status = "CONFIRMED"
        else:
            reg_status = "WAITLISTED"

        # Check if there was a previous CANCELLED registration for this user/event that we can reuse/reactivate
        cursor.execute(
            """
            SELECT reg_id, ticket_code FROM registrations 
            WHERE participant_id = ? AND event_id = ? AND status = 'CANCELLED'
            """,
            (participant_id, event_id)
        )
        cancelled_reg = cursor.fetchone()

        if cancelled_reg:
            reg_id = cancelled_reg["reg_id"]
            ticket_code = cancelled_reg["ticket_code"] or f"FEST-T{event_id}-{reg_id:04d}"
            cursor.execute(
                """
                UPDATE registrations 
                SET status = ?, ticket_code = ?, registered_at = ?
                WHERE reg_id = ?
                """,
                (reg_status, ticket_code, now_str, reg_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO registrations (event_id, participant_id, status, ticket_code, registered_at)
                VALUES (?, ?, ?, NULL, ?)
                """,
                (event_id, participant_id, reg_status, now_str)
            )
            reg_id = cursor.lastrowid
            ticket_code = f"FEST-T{event_id}-{reg_id:04d}"
            cursor.execute(
                "UPDATE registrations SET ticket_code = ? WHERE reg_id = ?",
                (ticket_code, reg_id)
            )

        conn.commit()

        if reg_status == "CONFIRMED":
            msg = (
                f"Registration Successful! {participant_name} is CONFIRMED for '{event_name}'. "
                f"Your Ticket Code is: {ticket_code}. "
                f"Venue: {event['venue']} on {event_date} from {start_time} to {end_time}."
            )
        else:
            msg = (
                f"Event '{event_name}' is currently FULL. {participant_name} has been placed on the WAITLIST. "
                f"Your Waitlist Tracking Code is: {ticket_code} (Note: This is NOT a confirmed entry ticket. "
                f"You will be automatically promoted if a seat opens up)."
            )

        return {
            "success": True,
            "status": reg_status,
            "ticket_code": ticket_code,
            "event_name": event_name,
            "event_date": event_date,
            "start_time": start_time,
            "end_time": end_time,
            "venue": event["venue"],
            "fee": float(event["fee"]),
            "message": msg
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Error registering for event: {str(e)}"
        }
    finally:
        conn.close()


# ============================================================================
# TOOL 4: cancel_registration
# ============================================================================
def cancel_registration(
    participant_email_or_id: str,
    event_name_or_id_or_reg_id: str
) -> Dict[str, Any]:
    """
    Cancel a participant's registration.
    Enforces Rule D: If the cancelled registration was CONFIRMED, the earliest
    eligible WAITLISTED participant is automatically promoted in the same transaction.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")

        # 1. Resolve participant
        participant = None
        if str(participant_email_or_id).isdigit():
            cursor.execute("SELECT * FROM participants WHERE participant_id = ?", (int(participant_email_or_id),))
            participant = cursor.fetchone()
        if not participant:
            norm_email = normalise_email(str(participant_email_or_id))
            cursor.execute("SELECT * FROM participants WHERE email = ?", (norm_email,))
            participant = cursor.fetchone()

        if not participant:
            conn.rollback()
            return {
                "success": False,
                "message": f"Participant '{participant_email_or_id}' was not found."
            }

        participant_id = participant["participant_id"]
        participant_name = participant["name"]

        # 2. Resolve the target registration
        target_str = str(event_name_or_id_or_reg_id).strip()
        reg = None

        # Check if argument is registration ID
        if target_str.isdigit():
            cursor.execute(
                """
                SELECT r.*, e.name AS event_name, e.event_date, e.start_time, e.end_time 
                FROM registrations r
                JOIN events e ON r.event_id = e.event_id
                WHERE r.reg_id = ? AND r.participant_id = ?
                """,
                (int(target_str), participant_id)
            )
            reg = cursor.fetchone()

        # If not found by reg_id, try event name or event ID
        if not reg:
            cursor.execute(
                """
                SELECT r.*, e.name AS event_name, e.event_date, e.start_time, e.end_time 
                FROM registrations r
                JOIN events e ON r.event_id = e.event_id
                WHERE r.participant_id = ? 
                  AND (LOWER(e.name) = LOWER(?) OR LOWER(e.name) LIKE LOWER(?) OR e.event_id = ?)
                ORDER BY r.reg_id DESC
                """,
                (participant_id, target_str, f"%{target_str}%", int(target_str) if target_str.isdigit() else -1)
            )
            reg = cursor.fetchone()

        if not reg:
            conn.rollback()
            return {
                "success": False,
                "message": f"No registration found for {participant_name} matching '{target_str}'."
            }

        reg_id = reg["reg_id"]
        event_id = reg["event_id"]
        event_name = reg["event_name"]
        event_date = reg["event_date"]
        start_time = reg["start_time"]
        end_time = reg["end_time"]
        prior_status = reg["status"]

        # 3. Status checks
        if prior_status == "CANCELLED":
            conn.rollback()
            return {
                "success": False,
                "message": f"Registration for '{event_name}' is already CANCELLED."
            }

        if prior_status == "CHECKED_IN":
            conn.rollback()
            return {
                "success": False,
                "message": f"Cannot cancel registration for '{event_name}': participant has already checked in."
            }

        # 4. Mark registration as CANCELLED
        cursor.execute(
            "UPDATE registrations SET status = 'CANCELLED' WHERE reg_id = ?",
            (reg_id,)
        )

        promoted_info = None

        # 5. Rule D: Automatic Waitlist Promotion if cancelled was CONFIRMED
        if prior_status == "CONFIRMED":
            # Find waitlisted participants ordered by registered_at ASC, reg_id ASC
            cursor.execute(
                """
                SELECT r.reg_id, r.participant_id, r.ticket_code, p.name AS candidate_name
                FROM registrations r
                JOIN participants p ON r.participant_id = p.participant_id
                WHERE r.event_id = ? AND r.status = 'WAITLISTED'
                ORDER BY r.registered_at ASC, r.reg_id ASC
                """,
                (event_id,)
            )
            waitlisted_candidates = cursor.fetchall()

            for cand in waitlisted_candidates:
                cand_reg_id = cand["reg_id"]
                cand_part_id = cand["participant_id"]
                cand_name = cand["candidate_name"]

                # Check Rule B: candidate has < 3 confirmed events
                cursor.execute(
                    """
                    SELECT COUNT(*) AS active_cnt 
                    FROM registrations 
                    WHERE participant_id = ? AND status IN ('CONFIRMED', 'CHECKED_IN')
                    """,
                    (cand_part_id,)
                )
                c_cnt = cursor.fetchone()["active_cnt"]
                if c_cnt >= 3:
                    # Ineligible due to max events rule; skip and evaluate next
                    continue

                # Check Rule A: candidate has no time-clash on event_date
                cursor.execute(
                    """
                    SELECT e.start_time, e.end_time 
                    FROM registrations r
                    JOIN events e ON r.event_id = e.event_id
                    WHERE r.participant_id = ? 
                      AND r.status IN ('CONFIRMED', 'CHECKED_IN')
                      AND e.event_date = ?
                    """,
                    (cand_part_id, event_date)
                )
                cand_events = cursor.fetchall()
                clash = False
                for ce in cand_events:
                    if start_time < ce["end_time"] and ce["start_time"] < end_time:
                        clash = True
                        break

                if clash:
                    # Ineligible due to clash; skip and evaluate next
                    continue

                # Eligible! Promote candidate in this same transaction
                cursor.execute(
                    "UPDATE registrations SET status = 'CONFIRMED' WHERE reg_id = ?",
                    (cand_reg_id,)
                )
                promoted_info = {
                    "participant_name": cand_name,
                    "ticket_code": cand["ticket_code"]
                }
                break  # Exactly one seat freed, so promote one participant

        conn.commit()

        msg = f"Registration for '{event_name}' (Ticket: {reg['ticket_code']}) has been successfully CANCELLED."
        if promoted_info:
            msg += (
                f" Automatic waitlist promotion (Rule D): Waitlisted participant "
                f"'{promoted_info['participant_name']}' has been promoted to CONFIRMED "
                f"(Ticket: {promoted_info['ticket_code']})."
            )

        return {
            "success": True,
            "message": msg,
            "cancelled_ticket": reg["ticket_code"],
            "event_name": event_name,
            "promoted": promoted_info
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Error cancelling registration: {str(e)}"
        }
    finally:
        conn.close()


# ============================================================================
# TOOL 5: get_my_registrations
# ============================================================================
def get_my_registrations(participant_email_or_id: str) -> Dict[str, Any]:
    """
    Retrieve all registrations (CONFIRMED, WAITLISTED, CHECKED_IN, CANCELLED)
    for a participant.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Resolve participant
        participant = None
        if str(participant_email_or_id).isdigit():
            cursor.execute("SELECT * FROM participants WHERE participant_id = ?", (int(participant_email_or_id),))
            participant = cursor.fetchone()
        if not participant:
            norm_email = normalise_email(str(participant_email_or_id))
            cursor.execute("SELECT * FROM participants WHERE email = ?", (norm_email,))
            participant = cursor.fetchone()

        if not participant:
            return {
                "success": False,
                "participant_found": False,
                "message": f"Participant '{participant_email_or_id}' not found. Would you like to register as a new participant?",
                "registrations": []
            }

        participant_id = participant["participant_id"]
        participant_name = participant["name"]

        cursor.execute(
            """
            SELECT 
                r.reg_id,
                r.ticket_code,
                r.status,
                r.registered_at,
                e.event_id,
                e.name AS event_name,
                e.category,
                e.venue,
                e.event_date,
                e.start_time,
                e.end_time,
                e.fee
            FROM registrations r
            JOIN events e ON r.event_id = e.event_id
            WHERE r.participant_id = ?
            ORDER BY e.event_date, e.start_time
            """,
            (participant_id,)
        )
        rows = cursor.fetchall()

        reg_list = []
        for r in rows:
            reg_list.append({
                "reg_id": r["reg_id"],
                "ticket_code": r["ticket_code"],
                "status": r["status"],
                "registered_at": r["registered_at"],
                "event_id": r["event_id"],
                "event_name": r["event_name"],
                "category": r["category"],
                "venue": r["venue"],
                "event_date": r["event_date"],
                "start_time": r["start_time"],
                "end_time": r["end_time"],
                "fee": float(r["fee"])
            })

        return {
            "success": True,
            "participant_found": True,
            "participant_name": participant_name,
            "email": participant["email"],
            "count": len(reg_list),
            "message": f"Found {len(reg_list)} registration(s) for {participant_name}.",
            "registrations": reg_list
        }
    finally:
        conn.close()


# ============================================================================
# TOOL 6: check_in
# ============================================================================
def check_in(ticket_code: str, is_organiser: bool = False) -> Dict[str, Any]:
    """
    Allow authorised organisers to check in participants using a ticket code.
    Enforces Rule E: One-time check-in, only for CONFIRMED registrations.
    """
    # Verify organiser authorisation in application code
    if not is_organiser:
        return {
            "success": False,
            "message": "Access Denied: Check-in is an organiser-only operation. Please log in as an organiser."
        }

    clean_code = str(ticket_code).strip()
    if not clean_code:
        return {
            "success": False,
            "message": "Ticket code cannot be empty."
        }

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION;")

        cursor.execute(
            """
            SELECT 
                r.reg_id,
                r.ticket_code,
                r.status,
                p.name AS participant_name,
                p.email AS participant_email,
                p.college,
                e.name AS event_name,
                e.venue,
                e.event_date,
                e.start_time,
                e.end_time
            FROM registrations r
            JOIN participants p ON r.participant_id = p.participant_id
            JOIN events e ON r.event_id = e.event_id
            WHERE UPPER(r.ticket_code) = UPPER(?)
            """,
            (clean_code,)
        )
        reg = cursor.fetchone()

        if not reg:
            conn.rollback()
            return {
                "success": False,
                "message": f"Ticket code '{clean_code}' not found. Please verify the code."
            }

        curr_status = reg["status"]

        if curr_status == "CHECKED_IN":
            conn.rollback()
            return {
                "success": False,
                "message": (
                    f"Check-In Rejected (Rule E): Ticket '{clean_code}' for {reg['participant_name']} "
                    f"has ALREADY been checked in. Duplicate check-ins are not permitted."
                )
            }

        if curr_status == "CANCELLED":
            conn.rollback()
            return {
                "success": False,
                "message": (
                    f"Check-In Rejected: Ticket '{clean_code}' belongs to a CANCELLED registration "
                    f"for '{reg['event_name']}'."
                )
            }

        if curr_status == "WAITLISTED":
            conn.rollback()
            return {
                "success": False,
                "message": (
                    f"Check-In Rejected: Ticket '{clean_code}' is WAITLISTED and has not received confirmed entry."
                )
            }

        if curr_status != "CONFIRMED":
            conn.rollback()
            return {
                "success": False,
                "message": f"Check-In Rejected: Ticket status is {curr_status}."
            }

        # Perform check-in
        cursor.execute(
            "UPDATE registrations SET status = 'CHECKED_IN' WHERE reg_id = ?",
            (reg["reg_id"],)
        )
        conn.commit()

        return {
            "success": True,
            "message": (
                f"Check-in Successful! Ticket: {reg['ticket_code']} | "
                f"Participant: {reg['participant_name']} ({reg['college']}) | "
                f"Event: {reg['event_name']} at {reg['venue']}."
            ),
            "ticket_code": reg["ticket_code"],
            "participant_name": reg["participant_name"],
            "event_name": reg["event_name"],
            "venue": reg["venue"]
        }
    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "message": f"Error during check-in: {str(e)}"
        }
    finally:
        conn.close()


# ============================================================================
# TOOL 7: event_stats
# ============================================================================
def event_stats(
    is_organiser: bool = False,
    longest_waitlist_only: bool = False
) -> Dict[str, Any]:
    """
    Provide organiser statistics:
    - Event capacity, confirmed, checked-in, waitlisted counts, available seats.
    - Identify the event with the longest waitlist (tie-breaker: event_id ASC).
    Enforces role-based authorization in application code.
    """
    if not is_organiser:
        return {
            "success": False,
            "message": "Access Denied: Event statistics are reserved for authorised organisers."
        }

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        query = """
            SELECT 
                e.event_id,
                e.name,
                e.category,
                e.venue,
                e.event_date,
                e.start_time,
                e.end_time,
                e.capacity,
                COALESCE(SUM(CASE WHEN r.status = 'CONFIRMED' THEN 1 ELSE 0 END), 0) AS confirmed_count,
                COALESCE(SUM(CASE WHEN r.status = 'CHECKED_IN' THEN 1 ELSE 0 END), 0) AS checked_in_count,
                COALESCE(SUM(CASE WHEN r.status = 'WAITLISTED' THEN 1 ELSE 0 END), 0) AS waitlisted_count
            FROM events e
            LEFT JOIN registrations r ON e.event_id = r.event_id
            GROUP BY e.event_id
            ORDER BY e.event_id ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        stats_list = []
        for r in rows:
            active_confirmed = r["confirmed_count"] + r["checked_in_count"]
            available = max(0, r["capacity"] - active_confirmed)
            stats_list.append({
                "event_id": r["event_id"],
                "name": r["name"],
                "category": r["category"],
                "venue": r["venue"],
                "event_date": r["event_date"],
                "start_time": r["start_time"],
                "end_time": r["end_time"],
                "capacity": r["capacity"],
                "confirmed_count": r["confirmed_count"],
                "checked_in_count": r["checked_in_count"],
                "waitlisted_count": r["waitlisted_count"],
                "available_seats": available
            })

        if longest_waitlist_only:
            # Deterministic tie-breaker: highest waitlisted_count DESC, event_id ASC
            sorted_by_waitlist = sorted(
                stats_list,
                key=lambda x: (-x["waitlisted_count"], x["event_id"])
            )
            top = sorted_by_waitlist[0] if sorted_by_waitlist else None
            if top and top["waitlisted_count"] > 0:
                msg = (
                    f"The event with the longest waitlist is '{top['name']}' (Event ID: {top['event_id']}) "
                    f"with {top['waitlisted_count']} participant(s) waiting."
                )
            elif top:
                msg = "There are currently no participants on the waitlist for any event."
            else:
                msg = "No events found in database."

            return {
                "success": True,
                "message": msg,
                "top_event": top
            }

        return {
            "success": True,
            "message": f"Retrieved statistics for {len(stats_list)} events.",
            "stats": stats_list
        }
    finally:
        conn.close()
