from playwright.async_api import async_playwright
import logging

from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
from typing import List

# Configure structured logging
logger = logging.getLogger(__name__) 
logger.setLevel(logging.INFO)


# Constants
_url = "https://www.albertahealthservices.ca/waittimes/Page14230.aspx"

class HospitalData(BaseModel):
    """A simple data class to hold hospital information we parse from ahs."""
    name: str = Field(description="The name of the hospital, e.g., 'Foothills Medical Centre'")
    city: str = Field(description="The city where the hospital is located, e.g., 'Calgary'")
    wait_time: str = Field(description="The wait time, e.g., '5 hr 43 min'")
    category: str = Field(description="The category of care, e.g., 'Emergency' or 'Urgent Care'")
    description: str = Field(description="A brief description of the hospital, e.g., 'Located in Calgary, offers a wide range of services...'")

# --- 1. THE PARSER FUNCTION ---
def parse_ahs_html(html_content: str, target_city: str) -> List[dict]:
    """
    Takes raw HTML containing the wait times and uses BeautifulSoup to extract the data.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    column_selector_em = f'div.cityContent-{target_city.lower().replace(" ", "")} div.waititems-Em'
    column_selector_ur = f'div.cityContent-{target_city.lower().replace(" ", "")} div.waititems-Ur'
    em_data = parse_hospital_data(soup, target_city, column_selector_em)

    if target_city.lower() == "calgary":
        # Only Calgary has the "Urgent Care" category, so we conditionally parse it
        ur_data = parse_hospital_data(soup, target_city, column_selector_ur)
        em_data.extend(ur_data)  # Combine both categories into one list

    return em_data

def parse_hospital_data(soup: BeautifulSoup, target_city: str, column_selector: str) -> List[dict]:
    """
    Helper function to parse either the Emergency or Urgent Care data based on the provided selector. 
    It returns a list of HospitalData objects.
    """
    hospital_data: List[HospitalData] = []
    row_selector = 'div.wt-well'
    name_selector = 'div.wt-description' # Example: The element with the text "Foothills Medical Centre"
    time_selector = 'div.wt-times > span'     # Example: The element with the text "5 hr 43 min"

    # Find all containers/rows that hold the data
    column = soup.select_one(column_selector)
    if not column:
        logger.info(f"No data found for selector: {column_selector}")
        return hospital_data
    rows = column.select(row_selector)
    for row in rows:
        try:
            name_elem = row.select_one(name_selector)
            time_elem = row.select_one(time_selector)
            if name_elem and time_elem:
                hour = time_elem.select_one('strong:nth-of-type(1)')
                minute = time_elem.select_one('strong:nth-of-type(2)')
                name = name_elem.select_one('p.hospitalName > strong > a')
                desc = name_elem.select_one('p.hospitalDesc')
                category = name_elem.select_one('p.hospitalCateg > span')
                if name and hour and minute and desc and category:
                    # Clean up the string (sometimes AHS adds extra whitespace or newlines)
                    name = " ".join(name.text.split())
                    wait_time = f"{hour.text.strip()} hr {minute.text.strip()} min"
                    data = HospitalData(
                        name=name,
                        city=target_city,
                        wait_time=wait_time,
                        category=category.text.strip(),
                        description=desc.text.strip() 
                    )
                    hospital_data.append(data.model_dump()) # Convert Pydantic model to dict for easier handling

        except AttributeError as e:
            logger.info(f"Skipping a row due to parsing error: {e}")
            continue

    return hospital_data

# --- 2. THE PLAYWRIGHT FETCH FUNCTION ---
async def fetch_ahs_wait_data(target_city: str = "Calgary") -> List[dict]:
    """
    Uses Playwright to load the AHS wait times page, select the city from the dropdown, and then extract the HTML content.
    The raw HTML is then passed to the parser function to extract structured hospital data.
    Note: The target_city should match the options available in the AHS dropdown (e.g., "Calgary", "Edmonton", etc.)
    """
    
    dropdown_id = "select#dd-city-ab" # The CSS selector for the city dropdown on the AHS wait times page

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            logger.info(f"Loading {_url}...")
            await page.goto(_url)
            
            logger.info(f"Selecting '{target_city}' from dropdown...")
            # Select the option by its visible text label
            await page.select_option(dropdown_id, value=target_city) # The value in the dropdown is usually the city name in lowercase with dashes instead of spaces
            
            # CRITICAL: We must wait for ASP.NET to finish the PostBack and re-render the DOM.
            # "networkidle" means wait until there are no more than 0 network connections for at least 500 ms.
            await page.wait_for_load_state("networkidle")
            
            # Optional: You can also explicitly wait for a specific element to appear to be safe
            # page.wait_for_selector('tr.wait-time-row', timeout=5000)

            logger.info("Data loaded. Extracting HTML...")
            raw_html = await page.content()
            
            # Pass the raw HTML into your BeautifulSoup function
            return parse_ahs_html(raw_html, target_city)

        except Exception as e:
            logger.error(f"Error during Playwright execution: {e}")
            return []
            
        finally:
            await browser.close()