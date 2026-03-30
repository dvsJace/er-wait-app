import sqlite3
import os
import logging

from app.database.read_repository import ReadRepository
from app.database.write_repository import WriteRepository

logger = logging.getLogger("app.database.sqlite_db")

# This matches the environment variable in your docker-compose.yml
DB_PATH = os.getenv("DATABASE_PATH", "/code/data/ahs_cache.db")

class UnitOfWork:
    """
    A simple Unit of Work pattern implementation for managing database transactions.
    """
    def __init__(self, db_path=DB_PATH):
        self.conn = None
        self.db_path = db_path

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        self.conn.isolation_level = None  # Autocommit mode

        # Init Repositories
        self.write_repository = WriteRepository(self.conn)
        self.read_repository = ReadRepository(self.conn)  # You can have separate read/write repos if you want
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Transaction failed: {exc_val}")
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()

def init_db():
    # Ensure the directory exists inside the container
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    logger.info(f"Initializing database at {DB_PATH}")
    
    with UnitOfWork() as uow:
        conn = uow.conn
    # 1. Reference table for hospital locations (The "Brain")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hospitals (
                name TEXT PRIMARY KEY,
                city TEXT,
                lat REAL,
                lon REAL,
                address TEXT,
                last_geocoded DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS hospital_wait_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                name TEXT,
                city TEXT,
                wait_time_str TEXT,
                wait_time_minutes INTEGER,
                category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(name) REFERENCES hospitals(name)
            )
        """)

        conn.execute("""
                DROP VIEW IF EXISTS v_hospital_trends;
        """)
        conn.execute("""
                CREATE VIEW IF NOT EXISTS v_hospital_trends AS
                WITH raw_deltas AS (
                    SELECT 
                        hwt.name as name,
                        hwt.city as city,
                        hwt.wait_time_minutes as wait_time_minutes,
                        hwt.timestamp as timestamp,
                        h.lat as lat,
                        h.lon as lon,
                        -- Get the wait time from the previous scrape for this specific hospital
                        LAG(hwt.wait_time_minutes) OVER (PARTITION BY hwt.name ORDER BY hwt.timestamp) as prev_wait
                    FROM hospital_wait_times hwt
                    JOIN hospitals h ON hwt.name = h.name
                )
                SELECT 
                    name,
                    city,
                    wait_time_minutes,
                    timestamp,
                    lat,
                    lon,
                    (wait_time_minutes - prev_wait) as delta,
                    CASE 
                        WHEN prev_wait IS NULL THEN 'New Data'
                        WHEN (wait_time_minutes - prev_wait) >= 20 THEN '⚠️ Spiking'
                        WHEN (wait_time_minutes - prev_wait) > 5   THEN '📈 Rising'
                        WHEN (wait_time_minutes - prev_wait) < -20 THEN '⚡ Clearing Fast'
                        WHEN (wait_time_minutes - prev_wait) < -5  THEN '📉 Improving'
                        ELSE '🟢 Stable'
                    END as trend_badge
                FROM raw_deltas
        """)

        conn.execute("""CREATE INDEX IF NOT EXISTS idx_hospital_time ON hospital_wait_times (name, timestamp DESC);""")
    logger.info("Database tables verified/created.")