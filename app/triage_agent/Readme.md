# Triage Agent
This agent takes user input, determines if the user input is health related, takes their info into a structured manner then it 
pulls the current AHS wait times data along with the users geolocation data which it uses to categorize the current hospitals relevant for the users location. It then responds to the user with a helpful message giving them info related to which hospital or urgent care will give them the best experience.


the agent should:

- Take user data related to location (address, city, province) and current reason for wanting to go to the ER.
- Determine if it should continue the flow or respond early to save tokens and then Parse out data into structured format
- Fetch current hospital wait times for city
- Categorize the hospitals to determine which one would be the most relevant for the user based on distance and wait time.
- Give the user a helpful message which gives them relevant information on which hospital is the closest / most fitting for their concern.


START 
Query User (user input step)
Determine & Parse (LLM step)
Fetch Hospital Data (data step)
Categorize Data (LLM Step)
Format and Send Reply (Action Step)
END