import logging
from typing import Optional, Tuple

from app.geocoding.nrcan_geolocation import get_coordinates_nrcan
from app.database.sqlite_db import UnitOfWork

logger = logging.getLogger("app.geocoding")

async def get_or_create_hospital_coords(uow: UnitOfWork, hospital_name: str, city: str)-> Tuple[Optional[float], Optional[float]]:
    """Checks the DB for coordinates, geocodes via NR Canada if missing."""
    logger.info(f"Checking cache for coordinates of {hospital_name} in {city}")
    res = uow.read_repository.get_lat_long_for_hospital(hospital_name)
    if res and all(res):
        logger.info(f"Cache hit for {hospital_name}: {res}")
        return float(res[0]), float(res[1])

    # --- Cache Miss: Ask NR Canada ---
    logger.info(f"Geocoding new hospital: {hospital_name} in {city}")
    try:
        lat, lon = await get_coordinates_nrcan(hospital_name, city)
        if lat and lon:
            # NR Canada returns [lon, lat]
            address = f"{hospital_name}, {city}, AB"
            # Save to reference table so we never have to geocode this again
            uow.write_repository.save_hospital_coordinates(hospital_name, city, lat, lon, address)
            return lat, lon
    except Exception as e:
        logger.error(f"Failed to geocode {hospital_name}: {e}")
    return None, None