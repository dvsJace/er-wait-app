from datetime import datetime
import logging
import re
import sqlite3
from typing import Optional
import uuid

logger = logging.getLogger("app.database.repository")

class WriteRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def save_hospital_wait_times_to_db(self, hospital_data_list: list[dict]):
        """
        Persists a batch of hospital data to SQLite.
        Each call to this function represents one 'snapshot' in time.
        """
        # Create a unique ID for this specific scrape session
        batch_id = str(uuid.uuid4())[:8] 
        timestamp = datetime.now().isoformat()
        cursor = self.conn.cursor()
        try:
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
            
        except sqlite3.Error as e:
            logger.error(f"Database insertion failed: {e}")
            raise e
        finally:
            cursor.close()
    def save_hospital_coordinates(self, hospital_name: str, city: str, lat: float, lon: float, address: str):
        """Saves geocoded hospital coordinates to the reference table."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO hospitals (name, city, lat, lon, address)
                VALUES (?, ?, ?, ?, ?)
            """, (hospital_name, city, lat, lon, address))
            self.conn.commit()
            logger.info(f"Saved coordinates for {hospital_name} in {city}: ({lat}, {lon})")
        except sqlite3.Error as e:
            logger.error(f"Failed to save coordinates for {hospital_name}: {e}")
            raise e
        finally:
            cursor.close()


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