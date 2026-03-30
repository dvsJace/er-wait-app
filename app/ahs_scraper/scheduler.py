from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scheduler.ahs_health_scraper import fetch_ahs_wait_data
from app.geocoding.geocoding import get_or_create_hospital_coords
from app.sqlite_db import save_to_db # The save function we discussed
import logging

logger = logging.getLogger("app.scheduler")
cities = ["Calgary", "Edmonton", "Red Deer", "Grande Prairie", "Lethbridge", "Medicine Hat", "Fort McMurray"] # List of cities to scrape
async def scrape_job():
    logger.info("--- Starting Periodic AHS Scrape ---")
    try:
        data = []
        for city in cities:
            hospital_wait_data = await fetch_ahs_wait_data(city)
            if hospital_wait_data:
                data.extend(hospital_wait_data)
            for hospital_data in hospital_wait_data:
                await get_or_create_hospital_coords(hospital_data['name'], city) # Geocode and cache coords for each hospital
        save_to_db(data)
        logger.info(f"Successfully cached {len(data)} hospitals.")
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Scrape every 10 minutes
    scheduler.add_job(scrape_job, 'interval', minutes=10)
    scheduler.start()
    return scheduler