from typing import Optional, Tuple
import httpx
import logging

logger = logging.getLogger(__name__)

# NRCAN endpoint for address geocoding
# https://natural-resources.canada.ca/maps-tools-publications/satellite-elevation-air-photos/geolocation-service
GEO_LOCATOR_URL = "https://geolocator.api.geo.ca/en/geolocation/address"

async def get_coordinates_nrcan(address: str, city: str) -> Optional[Tuple[float, float]]:
    """
    Fetches lat/lon for a Canadian address using the NRCAN Geolocation Service.
    """
    # Construct the query: "123 Main St, Calgary, AB"
    query = f"{address}, {city}, AB"
    
    params = {"q": query}

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(GEO_LOCATOR_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if not data or not isinstance(data, list):
                logger.warning(f"No results found for: {query}")
                return None, None

            # Grab the first match
            best_match = data[0]
            coords = best_match.get('geometry', {}).get('coordinates', [])

            if len(coords) >= 2:
                # NRCAN typically returns [longitude, latitude]
                lon_raw = coords[0]
                lat_raw = coords[1]

                # --- NUMERIC CHECK & VALIDATION ---
                try:
                    # We attempt to cast to float to handle cases where 
                    # numbers might arrive as strings (e.g., "-114.123")
                    lon = float(lon_raw)
                    lat = float(lat_raw)
                    
                    # Check for basic coordinate sanity (latitude -90 to 90, longitude -180 to 180)
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        logger.info(f"Validated coordinates for {query}: ({lat}, {lon})")
                        return lat, lon
                    else:
                        logger.error(f"Coordinates out of physical bounds: {lat}, {lon}")
                        
                except (ValueError, TypeError):
                    logger.error(f"Non-numeric coordinates received: lon={lon_raw}, lat={lat_raw}")

    except Exception as e:
        logger.error(f"NRCAN Geolocation API error: {e}")
    
    return None, None