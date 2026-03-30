from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.ahs_scraper.ahs_health_scraper import fetch_ahs_wait_data
from app.geocoding.geocoding import get_or_create_hospital_coords
from app.database.sqlite_db import UnitOfWork # The save function we discussed
import logging

logger = logging.getLogger("app.scheduler")
cities = ["Calgary", "Edmonton", "Red Deer", "Grande Prairie", "Lethbridge", "Medicine Hat", "Fort McMurray"] # List of cities to scrape
async def scrape_job():
    logger.info("--- Starting Periodic AHS Scrape ---")
    try:
        data = []
        for city in cities:
            with UnitOfWork() as uow:
                hospital_wait_data = await fetch_ahs_wait_data(city)
                if hospital_wait_data is None:
                    logger.warning(f"No data returned from scraper for {city}. Skipping.")
                    continue
                data.extend(hospital_wait_data)
                for hospital_data in hospital_wait_data:
                    await get_or_create_hospital_coords(uow, hospital_data['name'], city) # Geocode and cache coords for each hospital
                uow.write_repository.save_hospital_wait_times_to_db(data) # Save the scraped data to the DB
        logger.info(f"Successfully cached {len(data)} hospitals.")
    except Exception as e:
        logger.error(f"Scheduled scrape failed: {e}")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Scrape every 10 minutes
    scheduler.add_job(scrape_job, 'interval', minutes=10)
    scheduler.start()
    return scheduler