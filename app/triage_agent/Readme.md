the agent should:

- Take user data related to location (address, city, province) and current reason for wanting to go to the ER.
- Fetch current hospital wait times for city
- categorize the hospitals to determine which one would be the most relevant for the user based on distance and wait time.
- Give the user the categorize list of hospitals and their current wait times.


START 
Query User (user input step)
Fetch Hospital Data (data step)
Categorize Data (LLM Step)
Format and Send Reply (Action Step)
END