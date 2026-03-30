import logging
import sqlite3

logger = logging.getLogger("app.database.read_repository")

class ReadRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.conn = connection

    def get_latest_hospital_data(self, city: str) -> list[dict]:
        cursor = self.conn.cursor()
        try:
            # We find the latest timestamp for this specific city
            # Then we select all hospitals that match that timestamp and city
            query = """
                SELECT name, wait_time_minutes, trend_badge, timestamp, lat, lon
                FROM v_hospital_trends
                WHERE city = ? 
                AND timestamp = (SELECT MAX(timestamp) FROM v_hospital_trends WHERE city = ?)
            """
            rows = cursor.execute(query, (city.title(), city.title())).fetchall()
            
            # Convert SQLite rows to a list of dictionaries for the AI
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Database query failed for city {city}: {e}")
            raise e
        finally:
            cursor.close()

    def get_lat_long_for_hospital(self, hospital_name: str) -> tuple[float, float] | tuple[None, None]:
        cursor = self.conn.cursor()
        logger.info(f"Querying DB for coordinates of {hospital_name}")
        try:   
            query = "SELECT lat, lon FROM hospitals WHERE name = ?"
            res = cursor.execute(query, (hospital_name,)).fetchone()
            if res:
                logger.debug(f"DB returned coordinates for {hospital_name}: {res['lat']}, {res['lon']}")
                return res['lat'], res['lon']
            return None, None
        except sqlite3.Error as e:
            logger.error(f"Database query failed for {hospital_name}: {e}")
            raise e
        finally:
            cursor.close()