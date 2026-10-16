"""
database.py - SQLite Connection and Database Helper Functions
College Fest Event Registration Agent — EventEase
"""

import os
import sqlite3
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default SQLite database filename
DEFAULT_DB_PATH = "fest_events.db"


def get_db_path() -> str:
    """Return the database file path from environment or default."""
    return os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Establish a connection to SQLite database with foreign keys enabled
    and row factory configured for dictionary-like column access.
    """
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    
    # Enable foreign key constraint enforcement in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Return rows as sqlite3.Row objects so columns can be accessed by name
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None, schema_file: str = "schema.sql") -> None:
    """
    Initialise database tables, constraints, and indexes using schema.sql.
    """
    path = db_path or get_db_path()
    
    # Find schema.sql in current directory or script directory
    if not os.path.isabs(schema_file):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        schema_file = os.path.join(base_dir, schema_file)
        
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
        
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_db_connection(path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def reset_db(db_path: Optional[str] = None) -> None:
    """
    Safely reset the database by dropping existing tables and reinitialising.
    """
    path = db_path or get_db_path()
    conn = get_db_connection(path)
    try:
        # Drop existing tables in reverse dependency order
        conn.execute("DROP TABLE IF EXISTS registrations;")
        conn.execute("DROP TABLE IF EXISTS participants;")
        conn.execute("DROP TABLE IF EXISTS events;")
        conn.commit()
    finally:
        conn.close()
        
    # Recreate tables from schema
    init_db(path)


if __name__ == "__main__":
    print(f"Initialising database at {get_db_path()}...")
    init_db()
    print("Database initialised successfully.")
