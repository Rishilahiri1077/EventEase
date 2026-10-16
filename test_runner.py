"""
test_runner.py - Automated verification and test prompt runner for EventEase
Executes the five mandatory prompts and business rule violation tests,
recording expected vs actual outputs.
"""

import os
import sys
import json

# Ensure utf-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from seed import seed_database
from agent import EventEaseAgent, execute_pending_confirmation, get_fest_dates

def run_all_tests():
    print("=" * 70)
    print("Starting EventEase Automated Test Suite")
    print("=" * 70)

    # 1. Fresh database seed
    seed_database(reset=True)
    day1, day2 = get_fest_dates()
    print(f"Fest Dates: Day 1 = {day1}, Day 2 (Tomorrow) = {day2}\n")

    agent = EventEaseAgent()
    session_ctx = {"user_email": "riya@abc.edu"}
    test_results = {}

    # -------------------------------------------------------------------------
    # PROMPT 1: What tech events are happening tomorrow with seats left?
    # -------------------------------------------------------------------------
    p1 = "What tech events are happening tomorrow with seats left?"
    print(f"\n[TEST 1] User Prompt: \"{p1}\"")
    r1 = agent.process_message(p1, session_ctx, is_organiser=False)
    print("Agent Reply:\n" + r1["reply"])
    passed1 = "Hackathon" in r1["reply"] and "Robotics Workshop" in r1["reply"]
    print(f"Status: {'PASSED' if passed1 else 'FAILED'}")
    test_results["prompt_1"] = {
        "prompt": p1,
        "reply": r1["reply"],
        "passed": passed1
    }

    # -------------------------------------------------------------------------
    # PROMPT 2: Register me (riya@abc.edu) for the Hackathon and the Robo Race.
    # -------------------------------------------------------------------------
    p2 = "Register me (riya@abc.edu) for the Hackathon and the Robo Race."
    print(f"\n[TEST 2] User Prompt: \"{p2}\"")
    r2 = agent.process_message(p2, session_ctx, is_organiser=False)
    print("Confirmation Summary Proposed:\n" + r2["reply"])
    pending2 = r2.get("pending_confirmation")
    if pending2:
        confirm_reply2, success2 = execute_pending_confirmation(pending2, is_organiser=False)
        print("Final Execution After Confirmation:\n" + confirm_reply2)
        passed2 = success2 and "CONFIRMED" in confirm_reply2 and "Hackathon" in confirm_reply2 and "Robo Race" in confirm_reply2
    else:
        confirm_reply2 = "No confirmation triggered."
        passed2 = False
    print(f"Status: {'PASSED' if passed2 else 'FAILED'}")
    test_results["prompt_2"] = {
        "prompt": p2,
        "confirmation_step": r2["reply"],
        "final_reply": confirm_reply2,
        "passed": passed2
    }

    # -------------------------------------------------------------------------
    # PROMPT 3: Cancel my Robo Race registration.
    # -------------------------------------------------------------------------
    p3 = "Cancel my Robo Race registration."
    print(f"\n[TEST 3] User Prompt: \"{p3}\"")
    r3 = agent.process_message(p3, session_ctx, is_organiser=False)
    print("Confirmation Summary Proposed:\n" + r3["reply"])
    pending3 = r3.get("pending_confirmation")
    if pending3:
        confirm_reply3, success3 = execute_pending_confirmation(pending3, is_organiser=False)
        print("Final Execution After Confirmation:\n" + confirm_reply3)
        passed3 = success3 and "CANCELLED" in confirm_reply3
    else:
        confirm_reply3 = "No confirmation triggered."
        passed3 = False
    print(f"Status: {'PASSED' if passed3 else 'FAILED'}")
    test_results["prompt_3"] = {
        "prompt": p3,
        "confirmation_step": r3["reply"],
        "final_reply": confirm_reply3,
        "passed": passed3
    }

    # -------------------------------------------------------------------------
    # PROMPT 4: (Organiser) Check in ticket FEST-T7-0042.
    # -------------------------------------------------------------------------
    p4 = "(Organiser) Check in ticket FEST-T7-0042."
    print(f"\n[TEST 4] User Prompt: \"{p4}\"")
    
    # First test unauthenticated
    r4_unauth = agent.process_message(p4, session_ctx, is_organiser=False)
    print("Unauthenticated Check-in Reply (RBAC test):\n" + r4_unauth["reply"])
    unauth_blocked = "Access Denied" in r4_unauth["reply"]

    # Now test authenticated organiser
    r4 = agent.process_message(p4, session_ctx, is_organiser=True)
    print("Confirmation Summary Proposed:\n" + r4["reply"])
    pending4 = r4.get("pending_confirmation")
    if pending4:
        confirm_reply4, success4 = execute_pending_confirmation(pending4, is_organiser=True)
        print("Final Execution After Confirmation:\n" + confirm_reply4)
        passed4 = unauth_blocked and success4 and "Check-in Successful" in confirm_reply4
    else:
        confirm_reply4 = "No confirmation triggered."
        passed4 = False
    print(f"Status: {'PASSED' if passed4 else 'FAILED'}")
    test_results["prompt_4"] = {
        "prompt": p4,
        "unauth_reply": r4_unauth["reply"],
        "confirmation_step": r4["reply"],
        "final_reply": confirm_reply4,
        "passed": passed4
    }

    # -------------------------------------------------------------------------
    # PROMPT 5: (Organiser) Which event has the longest waitlist?
    # -------------------------------------------------------------------------
    p5 = "(Organiser) Which event has the longest waitlist?"
    print(f"\n[TEST 5] User Prompt: \"{p5}\"")
    
    # Test unauthenticated access block
    r5_unauth = agent.process_message(p5, session_ctx, is_organiser=False)
    print("Unauthenticated Waitlist Query Reply (RBAC test):\n" + r5_unauth["reply"])
    unauth_blocked_5 = any(term in r5_unauth["reply"].lower() for term in ["access denied", "organiser", "restricted", "unauthorised"])

    # Test authenticated organiser access
    r5 = agent.process_message(p5, session_ctx, is_organiser=True)
    print("Authenticated Organiser Reply:\n" + r5["reply"])
    passed5 = unauth_blocked_5 and "Cricket Tournament" in r5["reply"] and "5" in r5["reply"]
    print(f"Status: {'PASSED' if passed5 else 'FAILED'}")
    test_results["prompt_5"] = {
        "prompt": p5,
        "unauth_reply": r5_unauth["reply"],
        "reply": r5["reply"],
        "passed": passed5
    }

    # -------------------------------------------------------------------------
    # BUSINESS RULE VIOLATION TEST 1: Schedule Clash (Rule A)
    # -------------------------------------------------------------------------
    print("\n[BUSINESS RULE TEST 1] Attempting to register for overlapping events (Time Clash)")
    import tools
    # Riya Sharma registers for Robo Race (10:00 - 12:00 on Day 1)
    tools.register_for_event("riya@abc.edu", "Robo Race")
    # Now attempts to register for Coding Challenge (11:00 - 13:00 on Day 1) -> Overlaps!
    res_clash = tools.register_for_event("riya@abc.edu", "Coding Challenge")
    print("Rule A Result:", res_clash["message"])
    passed_rule_a = not res_clash["success"] and "Schedule Clash" in res_clash["message"]
    print(f"Status: {'PASSED' if passed_rule_a else 'FAILED'}")

    # -------------------------------------------------------------------------
    # BUSINESS RULE VIOLATION TEST 2: Max Three Confirmed Events (Rule B)
    # -------------------------------------------------------------------------
    print("\n[BUSINESS RULE TEST 2] Attempting to register for a 4th confirmed event (Rule B)")
    # Riya currently has: Hackathon (from Test 2, Day 2) and Robo Race (Day 1) -> 2 confirmed
    tools.register_for_event("riya@abc.edu", "Dance Battle") # 3rd confirmed
    # Now attempt 4th confirmed event
    res_max = tools.register_for_event("riya@abc.edu", "Street Play")
    print("Rule B Result:", res_max["message"])
    passed_rule_b = not res_max["success"] and "Limit Exceeded" in res_max["message"]
    print(f"Status: {'PASSED' if passed_rule_b else 'FAILED'}")

    # -------------------------------------------------------------------------
    # BUSINESS RULE VIOLATION TEST 3: Duplicate Active Registration (Rule C)
    # -------------------------------------------------------------------------
    print("\n[BUSINESS RULE TEST 3] Attempting duplicate registration (Rule C)")
    res_dup = tools.register_for_event("riya@abc.edu", "Robo Race")
    print("Rule C Result:", res_dup["message"])
    passed_rule_c = not res_dup["success"] and "Duplicate Registration Blocked" in res_dup["message"]
    print(f"Status: {'PASSED' if passed_rule_c else 'FAILED'}")

    # -------------------------------------------------------------------------
    # BUSINESS RULE TEST 4: Automatic Waitlist Promotion (Rule D)
    # -------------------------------------------------------------------------
    print("\n[BUSINESS RULE TEST 4] Automatic Waitlist Promotion on Cancellation (Rule D)")
    # Event 10 (Singing Competition) is full. Participant 18 cancels -> Participant 28 (Fatima Sana) promoted
    res_promo = tools.cancel_registration("neha.k@music.edu", "Singing Competition")
    print("Rule D Result:", res_promo["message"])
    passed_rule_d = res_promo["success"] and res_promo.get("promoted") is not None
    print(f"Status: {'PASSED' if passed_rule_d else 'FAILED'}")

    # -------------------------------------------------------------------------
    # BUSINESS RULE TEST 5: One-Time Check-In (Rule E)
    # -------------------------------------------------------------------------
    print("\n[BUSINESS RULE TEST 5] One-Time Check-In (Rule E)")
    # FEST-T7-0042 was checked in during Test 4. Attempt second check-in:
    res_dup_checkin = tools.check_in("FEST-T7-0042", is_organiser=True)
    print("Rule E Result:", res_dup_checkin["message"])
    passed_rule_e = not res_dup_checkin["success"] and "ALREADY been checked in" in res_dup_checkin["message"]
    print(f"Status: {'PASSED' if passed_rule_e else 'FAILED'}")

    all_passed = all([
        passed1, passed2, passed3, passed4, passed5,
        passed_rule_a, passed_rule_b, passed_rule_c, passed_rule_d, passed_rule_e
    ])

    print("\n" + "=" * 70)
    print(f"OVERALL TEST SUITE: {'ALL TESTS PASSED ✅' if all_passed else 'SOME TESTS FAILED ❌'}")
    print("=" * 70)
    return test_results

if __name__ == "__main__":
    run_all_tests()
