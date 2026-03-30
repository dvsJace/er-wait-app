import datetime
import sqlite3
import os
import logging
import uuid
import re
from typing import Optional

logger = logging.getLogger("app.database")

# This matches the environment variable in your docker-compose.yml
DB_PATH = os.getenv("DATABASE_PATH", "/code/data/ahs_cache.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def init_db():
    # Ensure the directory exists inside the container
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    logger.info(f"Initializing database at {DB_PATH}")
    
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hospital_wait_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                name TEXT,
                city TEXT,
                wait_time_str TEXT,
                wait_time_minutes INTEGER,
                category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    logger.info("Database tables verified/created.")


def get_latest_cached_data() -> list:
    with get_db_connection() as conn:
        # Check for data from the last 10 minutes
        ten_mins_ago = (datetime.now() - datetime.timedelta(minutes=10)).isoformat()
        
        query = "SELECT * FROM hospital_wait_times WHERE timestamp > ? ORDER BY timestamp DESC"
        results = conn.execute(query, (ten_mins_ago,)).fetchall()
        
        if results:
            return [dict(row) for row in results]
    return None # Trigger a fresh scrape if None

def get_latest_hospital_data(city: str):
    """
    Retrieves the most recent batch of hospital data for a specific city.
    """
    with get_db_connection() as conn:
        # We find the latest timestamp for this specific city
        # Then we select all hospitals that match that timestamp and city
        query = """
            SELECT name, wait_time_str, wait_time_minutes, category, timestamp
            FROM hospital_wait_times
            WHERE city = ? 
            AND timestamp = (
                SELECT MAX(timestamp) 
                FROM hospital_wait_times 
                WHERE city = ?
            )
        """
        rows = conn.execute(query, (city.title(), city.title())).fetchall()
        
        # Convert SQLite rows to a list of dictionaries for the AI
        return [dict(row) for row in rows]


def parse_wait_time_to_minutes(wait_str: str) -> Optional[int]:
    """
    Parses AHS wait time strings into integer minutes.
    Example: '1 hr 45 min' -> 105
    Example: '25 min' -> 25
    """
    if not wait_str or not isinstance(wait_str, str):
        return None

    wait_str = wait_str.lower().strip()
    
    # Handle 'unavailable' or 'see staff' cases
    if any(word in wait_str for word in ["unavailable", "see", "n/a"]):
        return None

    total_minutes = 0
    found_any = False

    # 1. Regex for Hours: looks for a digit followed by 'hr'
    hr_match = re.search(r'(\d+)\s*hr', wait_str)
    if hr_match:
        total_minutes += int(hr_match.group(1)) * 60
        found_any = True

    # 2. Regex for Minutes: looks for a digit followed by 'min'
    min_match = re.search(r'(\d+)\s*min', wait_str)
    if min_match:
        total_minutes += int(min_match.group(1))
        found_any = True

    # If we found neither hours nor minutes, it's unparseable
    return total_minutes if found_any else None

def save_to_db(hospital_data_list: list[dict]):
    """
    Persists a batch of hospital data to SQLite.
    Each call to this function represents one 'snapshot' in time.
    """
    # Create a unique ID for this specific scrape session
    batch_id = str(uuid.uuid4())[:8] 
    timestamp = datetime.datetime.now().isoformat()
    logger.info(f"Saving batch {batch_id} with {len(hospital_data_list)} hospital entries at {timestamp}")
    logger.debug(f"Hospital data being saved: {hospital_data_list}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for hospital in hospital_data_list:
                # Convert "5 hr 30 min" -> 330 (integer) for math/trends
                wait_minutes = parse_wait_time_to_minutes(hospital.get('wait_time', ''))
                
                cursor.execute("""
                    INSERT INTO hospital_wait_times (
                        batch_id, 
                        name,
                        city,
                        wait_time_str, 
                        wait_time_minutes, 
                        category, 
                        timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    batch_id,
                    hospital.get('name'),
                    hospital.get('city'),
                    hospital.get('wait_time'),
                    wait_minutes,
                    hospital.get('category'),
                    timestamp
                ))
            
            conn.commit()
            logger.info(f"Batch {batch_id} saved: {len(hospital_data_list)} hospitals recorded.")
            
    except sqlite3.Error as e:
        logger.error(f"Database insertion failed: {e}")