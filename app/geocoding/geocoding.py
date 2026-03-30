import logging
from typing import Optional, Tuple

from app.geocoding.nrcan_geolocation import get_coordinates_nrcan
from app.sqlite_db import get_db_connection

logger = logging.getLogger("app.geocoding")

async def get_or_create_hospital_coords(hospital_name: str, city: str)-> Tuple[Optional[float], Optional[float]]:
    """Checks the DB for coordinates, geocodes via NR Canada if missing."""
    
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT lat, lon FROM hospitals WHERE name = ?", (hospital_name,)
        ).fetchone()
        
        if res:
            return res['lat'], res['lon']

    # --- Cache Miss: Ask NR Canada ---
    logger.info(f"Geocoding new hospital: {hospital_name} in {city}")

    try:
        lat, lon = await get_coordinates_nrcan(hospital_name, city)
        logger.info(f"NRCAN geocoding result for {hospital_name}: ({lat}, {lon})")
        if lat and lon:
            # NR Canada returns [lon, lat]
            address = f"{hospital_name}, {city}, AB"
            
            # Save to reference table so we never have to geocode this again
            with get_db_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO hospitals (name, city, lat, lon, address)
                    VALUES (?, ?, ?, ?, ?)
                """, (hospital_name, city, lat, lon, address))
                conn.commit()
            
            return lat, lon
    except Exception as e:
        logger.error(f"Failed to geocode {hospital_name}: {e}")
            
    return None, None