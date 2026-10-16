-- ============================================================================
-- College Fest Event Registration Agent — EventEase
-- schema.sql: Database schema, tables, constraints, indexes, and relationships
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- Table: events
-- Stores all college fest events with schedule, capacity, and category
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('TECH', 'CULTURAL', 'SPORTS')),
    venue TEXT NOT NULL,
    event_date TEXT NOT NULL,       -- YYYY-MM-DD
    start_time TEXT NOT NULL,       -- HH:MM
    end_time TEXT NOT NULL,         -- HH:MM
    capacity INTEGER NOT NULL CHECK(capacity > 0),
    fee REAL NOT NULL CHECK(fee >= 0.0)
);

-- ----------------------------------------------------------------------------
-- Table: participants
-- Stores participant profiles with normalised unique email addresses
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS participants (
    participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,     -- Lowercase and trimmed
    college TEXT NOT NULL,
    phone TEXT NOT NULL
);

-- ----------------------------------------------------------------------------
-- Table: registrations
-- Stores event registrations, statuses, timestamps, and unique ticket codes
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS registrations (
    reg_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    participant_id INTEGER NOT NULL REFERENCES participants(participant_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK(status IN ('CONFIRMED', 'WAITLISTED', 'CANCELLED', 'CHECKED_IN')),
    ticket_code TEXT UNIQUE,
    registered_at TEXT NOT NULL     -- ISO-8601 string: YYYY-MM-DDTHH:MM:SS
);

-- ----------------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------------
-- Prevent duplicate active registrations for the same participant and event.
-- Cancelled registrations are excluded, allowing reactivation.
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_reg 
    ON registrations(participant_id, event_id) 
    WHERE status != 'CANCELLED';

CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
CREATE INDEX IF NOT EXISTS idx_registrations_status ON registrations(status);
CREATE INDEX IF NOT EXISTS idx_registrations_event ON registrations(event_id);
CREATE INDEX IF NOT EXISTS idx_registrations_participant ON registrations(participant_id);
CREATE INDEX IF NOT EXISTS idx_registrations_ticket ON registrations(ticket_code);
