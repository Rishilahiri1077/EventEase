"""
seed.py - Reproducible Database Seeder for EventEase
College Fest Event Registration Agent — EventEase
"""

import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from database import reset_db, get_db_connection

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


def seed_database(reset: bool = True) -> None:
    """
    Populate the SQLite database with rich, realistic, reproducible test data.
    - 14 events spread across two fest days (today and tomorrow in Asia/Kolkata)
    - All categories: TECH, CULTURAL, SPORTS
    - Mix of capacities (including capacity 5, available seats, and full events)
    - 32 participants (including Riya Sharma riya@abc.edu)
    - 46 registrations (CONFIRMED, WAITLISTED, CANCELLED, CHECKED_IN)
    - Longest waitlist on Cricket Tournament
    - Overlapping events for schedule clash testing
    - Guaranteed ticket FEST-T7-0042 for event 7 (Hackathon) with CONFIRMED status
    """
    if reset:
        print("Resetting database...")
        reset_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine dynamic fest dates: Day 1 = Today, Day 2 = Tomorrow (Asia/Kolkata)
    base_date_env = os.getenv("FEST_BASE_DATE")
    if base_date_env:
        today = datetime.strptime(base_date_env, "%Y-%m-%d").date()
    else:
        today = datetime.now(KOLKATA_TZ).date()

    tomorrow = today + timedelta(days=1)
    day1_str = today.strftime("%Y-%m-%d")
    day2_str = tomorrow.strftime("%Y-%m-%d")

    print(f"Fest Dates: Day 1 = {day1_str}, Day 2 (Tomorrow) = {day2_str}")

    # -------------------------------------------------------------------------
    # 1. Seed Events (14 events: 6 on Day 1, 8 on Day 2)
    # -------------------------------------------------------------------------
    events = [
        # Day 1 Events
        (1, "Robo Race", "TECH", "Tech Arena", day1_str, "10:00", "12:00", 5, 100.0),
        (2, "Coding Challenge", "TECH", "Computer Lab 3", day1_str, "11:00", "13:00", 5, 50.0), # Overlaps Robo Race
        (3, "Dance Battle", "CULTURAL", "Main Auditorium Stage", day1_str, "14:00", "17:00", 10, 0.0),
        (4, "BGMI Tournament", "SPORTS", "Seminar Hall A", day1_str, "15:00", "18:00", 5, 200.0),
        (5, "Street Play", "CULTURAL", "Open Amphitheatre", day1_str, "17:00", "19:00", 8, 0.0),
        (6, "Table Tennis Blitz", "SPORTS", "Indoor Sports Complex", day1_str, "10:00", "13:00", 6, 50.0),

        # Day 2 Events (Tomorrow)
        (7, "Hackathon", "TECH", "Innovation Hub", day2_str, "09:00", "17:00", 20, 150.0),
        (8, "Robotics Workshop", "TECH", "Mechanical Lab", day2_str, "10:00", "13:00", 15, 100.0),
        (9, "Web Dev Sprint", "TECH", "Computer Lab 1", day2_str, "14:00", "16:30", 5, 0.0),
        (10, "Singing Competition", "CULTURAL", "Music Hall", day2_str, "11:00", "14:00", 5, 0.0),
        (11, "Fashion Show", "CULTURAL", "Main Auditorium Stage", day2_str, "16:00", "19:00", 12, 100.0),
        (12, "Cricket Tournament", "SPORTS", "Main Sports Ground", day2_str, "09:00", "15:00", 8, 300.0),
        (13, "Chess Championship", "SPORTS", "Student Activity Center", day2_str, "14:00", "17:00", 5, 0.0),
        (14, "AI Showcase", "TECH", "Tech Arena", day2_str, "15:00", "18:00", 5, 50.0),
    ]

    cursor.executemany(
        """
        INSERT INTO events (event_id, name, category, venue, event_date, start_time, end_time, capacity, fee)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        events
    )
    print(f"Inserted {len(events)} events.")

    # -------------------------------------------------------------------------
    # 2. Seed Participants (32 participants)
    # -------------------------------------------------------------------------
    participants = [
        (1, "Riya Sharma", "riya@abc.edu", "ABC College of Engineering", "9876543210"),
        (2, "Aarav Patel", "aarav.patel@xyz.edu", "XYZ Institute of Tech", "9876543211"),
        (3, "Ananya Iyer", "ananya.iyer@pqr.edu", "PQR Engineering College", "9876543212"),
        (4, "Rohan Mehta", "rohan.mehta@abc.edu", "ABC College of Engineering", "9876543213"),
        (5, "Sneha Rao", "sneha.rao@lmn.edu", "LMN University", "9876543214"),
        (6, "Aditya Verma", "aditya.v@xyz.edu", "XYZ Institute of Tech", "9876543215"),
        (7, "Priya Nair", "priya.nair@pqr.edu", "PQR Engineering College", "9876543216"),
        (8, "Karan Joshi", "karan.j@abc.edu", "ABC College of Engineering", "9876543217"),
        (9, "Tanvi Deshmukh", "tanvi.d@lmn.edu", "LMN University", "9876543218"),
        (10, "Kabir Singh", "kabir.s@xyz.edu", "XYZ Institute of Tech", "9876543219"),
        (11, "Ishaan Gupta", "ishaan.g@pqr.edu", "PQR Engineering College", "9876543220"),
        (12, "Diya Kapoor", "diya.k@abc.edu", "ABC College of Engineering", "9876543221"),
        (13, "Arjun Reddy", "arjun.r@lmn.edu", "LMN University", "9876543222"),
        (14, "Meera Nambiar", "meera.n@xyz.edu", "XYZ Institute of Tech", "9876543223"),
        (15, "Siddharth Roy", "siddharth.r@pqr.edu", "PQR Engineering College", "9876543224"),
        (16, "Pooja Hegde", "pooja.h@abc.edu", "ABC College of Engineering", "9876543225"),
        (17, "Rahul Dravid", "rahul.d@sports.edu", "National Sports Academy", "9876543226"),
        (18, "Neha Kakkar", "neha.k@music.edu", "College of Fine Arts", "9876543227"),
        (19, "Aman Roy", "aman.roy@xyz.edu", "XYZ Institute of Tech", "9876543228"),
        (20, "Shreya Ghoshal", "shreya.g@music.edu", "College of Fine Arts", "9876543229"),
        (21, "Varun Dhawan", "varun.d@arts.edu", "City Arts College", "9876543230"),
        (22, "Alia Bhatt", "alia.b@arts.edu", "City Arts College", "9876543231"),
        (23, "Devansh Shah", "devansh.s@abc.edu", "ABC College of Engineering", "9876543232"),
        (24, "Kriti Sanon", "kriti.s@lmn.edu", "LMN University", "9876543233"),
        (25, "Yashvardhan Rao", "yash.r@pqr.edu", "PQR Engineering College", "9876543234"),
        (26, "Simran Kaur", "simran.k@xyz.edu", "XYZ Institute of Tech", "9876543235"),
        (27, "Ayushmann K", "ayushmann.k@arts.edu", "City Arts College", "9876543236"),
        (28, "Fatima Sana", "fatima.s@lmn.edu", "LMN University", "9876543237"),
        (29, "Rajkummar Rao", "raj.rao@arts.edu", "City Arts College", "9876543238"),
        (30, "Sanya Malhotra", "sanya.m@abc.edu", "ABC College of Engineering", "9876543239"),
        (31, "Vicky Kaushal", "vicky.k@pqr.edu", "PQR Engineering College", "9876543240"),
        (32, "Vikram Malhotra", "vikram.m@xyz.edu", "XYZ Institute of Tech", "9876543241"),
    ]

    cursor.executemany(
        """
        INSERT INTO participants (participant_id, name, email, college, phone)
        VALUES (?, ?, ?, ?, ?)
        """,
        participants
    )
    print(f"Inserted {len(participants)} participants.")

    # -------------------------------------------------------------------------
    # 3. Seed Registrations (46 registrations)
    # -------------------------------------------------------------------------
    # Format: (reg_id, event_id, participant_id, status, ticket_code, timestamp_offset_mins)
    base_ts = datetime(2026, 10, 15, 9, 0, 0, tzinfo=KOLKATA_TZ)

    reg_defs = [
        # Event 1: Robo Race (Cap: 5) -> 2 confirmed, 3 seats available for testing
        (1, 1, 2, "CONFIRMED", "FEST-T1-0001", 10),
        (2, 1, 3, "CONFIRMED", "FEST-T1-0002", 20),
        (3, 1, 4, "CANCELLED", "FEST-T1-0003", 30), # Cancelled registration

        # Event 2: Coding Challenge (Cap: 5)
        (4, 2, 5, "CONFIRMED", "FEST-T2-0004", 40),
        (5, 2, 6, "CONFIRMED", "FEST-T2-0005", 50),

        # Event 3: Dance Battle (Cap: 10)
        (6, 3, 2, "CONFIRMED", "FEST-T3-0006", 60), # Participant 2 multi-event test
        (7, 3, 7, "CONFIRMED", "FEST-T3-0007", 70),
        (8, 3, 8, "CHECKED_IN", "FEST-T3-0008", 80), # Checked in registration

        # Event 4: BGMI Tournament (Cap: 5)
        (9, 4, 9, "CONFIRMED", "FEST-T4-0009", 90),
        (10, 4, 10, "CONFIRMED", "FEST-T4-0010", 100),

        # Event 6: Table Tennis Blitz (Cap: 6)
        (11, 6, 11, "CONFIRMED", "FEST-T6-0011", 110),
        (12, 6, 12, "CONFIRMED", "FEST-T6-0012", 120),

        # Event 10: Singing Competition (Cap: 5) -> FULL (5 Confirmed + 3 Waitlisted)
        (13, 10, 18, "CONFIRMED", "FEST-T10-0013", 130),
        (14, 10, 20, "CONFIRMED", "FEST-T10-0014", 140),
        (15, 10, 21, "CONFIRMED", "FEST-T10-0015", 150),
        (16, 10, 22, "CONFIRMED", "FEST-T10-0016", 160),
        (17, 10, 27, "CONFIRMED", "FEST-T10-0017", 170),
        (18, 10, 28, "WAITLISTED", "FEST-T10-0018", 180),
        (19, 10, 29, "WAITLISTED", "FEST-T10-0019", 190),
        (20, 10, 30, "WAITLISTED", "FEST-T10-0020", 200),

        # Event 12: Cricket Tournament (Cap: 8) -> FULL (8 Confirmed + 5 Waitlisted)
        # LONGEST WAITLIST in the fest!
        (21, 12, 6, "CONFIRMED", "FEST-T12-0021", 210),
        (22, 12, 8, "CONFIRMED", "FEST-T12-0022", 220),
        (23, 12, 10, "CONFIRMED", "FEST-T12-0023", 230),
        (24, 12, 13, "CONFIRMED", "FEST-T12-0024", 240),
        (25, 12, 14, "CONFIRMED", "FEST-T12-0025", 250),
        (26, 12, 15, "CONFIRMED", "FEST-T12-0026", 260),
        (27, 12, 16, "CONFIRMED", "FEST-T12-0027", 270),
        (28, 12, 17, "CONFIRMED", "FEST-T12-0028", 280),
        (29, 12, 19, "WAITLISTED", "FEST-T12-0029", 290),
        (30, 12, 23, "WAITLISTED", "FEST-T12-0030", 300),
        (31, 12, 24, "WAITLISTED", "FEST-T12-0031", 310),
        (32, 12, 25, "WAITLISTED", "FEST-T12-0032", 320),
        (33, 12, 26, "WAITLISTED", "FEST-T12-0033", 330),

        # Event 14: AI Showcase (Cap: 5) -> FULL (5 Confirmed + 2 Waitlisted)
        (34, 14, 5, "CONFIRMED", "FEST-T14-0034", 340),
        (35, 14, 7, "CONFIRMED", "FEST-T14-0035", 350),
        (36, 14, 9, "CONFIRMED", "FEST-T14-0036", 360),
        (37, 14, 11, "CONFIRMED", "FEST-T14-0037", 370),
        (38, 14, 12, "CONFIRMED", "FEST-T14-0038", 380),
        (39, 14, 31, "WAITLISTED", "FEST-T14-0039", 390),
        (40, 14, 13, "WAITLISTED", "FEST-T14-0040", 400),

        # Event 7: Hackathon (Cap: 20) -> Has available seats (8 Confirmed, 12 Available)
        (41, 7, 2, "CONFIRMED", "FEST-T7-0041", 410),
        # Mandatory test ticket: FEST-T7-0042 assigned to participant 32 (Vikram Malhotra), CONFIRMED
        (42, 7, 32, "CONFIRMED", "FEST-T7-0042", 420),
        (43, 7, 4, "CONFIRMED", "FEST-T7-0043", 430),
        (44, 7, 5, "CONFIRMED", "FEST-T7-0044", 440),
        (45, 7, 14, "CONFIRMED", "FEST-T7-0045", 450),
        (46, 7, 15, "CONFIRMED", "FEST-T7-0046", 460),
    ]

    registrations = []
    for reg_id, event_id, part_id, status, code, mins in reg_defs:
        reg_time = (base_ts + timedelta(minutes=mins)).strftime("%Y-%m-%dT%H:%M:%S")
        registrations.append((reg_id, event_id, part_id, status, code, reg_time))

    cursor.executemany(
        """
        INSERT INTO registrations (reg_id, event_id, participant_id, status, ticket_code, registered_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        registrations
    )
    print(f"Inserted {len(registrations)} registrations.")

    conn.commit()
    conn.close()

    print("Seed data loaded successfully!")
    print(f"  Total Events: {len(events)}")
    print(f"  Total Participants: {len(participants)}")
    print(f"  Total Registrations: {len(registrations)}")
    print("  Ticket 'FEST-T7-0042' is CONFIRMED for Hackathon (Event 7).")
    print("  Riya Sharma (riya@abc.edu) is ready for test registrations.")


if __name__ == "__main__":
    reset_arg = "--no-reset" not in sys.argv
    seed_database(reset=reset_arg)
