import logging
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import SlotSet
import json
import re
import requests
from bs4 import BeautifulSoup
import openai
import os
logging.basicConfig(level=logging.INFO, filename='actions.log', filemode='a', encoding='utf-8',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Replace YOUR_API_KEY with the actual key you want to remove

class ActionGreet(Action):

    def name(self) -> str:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        print(F"COMING INSIDE-------------------------------->")
        dispatcher.utter_message(text="Hello and welcome to the Facebook Ad Campaign Creator. I'm here to assist you in creating a successful ad campaign for your property. Please provide the project URL or a brief description, including essential details such as Name Brand Location Type Subtype Sizes Prices Offers Key amenities RERA Number and any other relevant information")
        return []
    

class ActionScrapeUrl(Action):
    def name(self) -> Text:
        return "action_scrape_url"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_message = tracker.latest_message.get('text')
        url = re.search(r'http[s]?://[^\s]+', user_message)
        print(f"INSIDE SCRAPE URL")
        try:
        
            if url:
                url = url.group(0)
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                data = soup.get_text()
                data = re.sub(r'\s+', ' ', data).strip()
            else:
                data = user_message
            
            trimmed_data = data[:4000]
            prompt = f"""
            Here is the data from the website:

            {trimmed_data}

            Extract the following information if available:
            - Name
            - Brand
            - Location
            - Type
            - Subtype
            - Sizes
            - Prices
            - Offers (e.g., payment plans)
            - Key amenities
            - RERA Number
            # Provide the extracted information in a structured json format.
            """
            
            openai.api_key = os.getenv('OPENAI_API_KEY')  # Replace with your actual API key

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )

            # Step 5: Extract and Print the Response
            global extracted_info
            extracted_info= response.choices[0].message['content'].strip()
            print(f"THE OUTPUT IS--->{extracted_info}")
            logger.info(f"THE EXTRACTED OUTPUT IS------->{extracted_info}<--{type(extracted_info)}-")
            prompt2 = f"""
            here is the extracted data {extracted_info} convert this into a string printable format
            """
            response2 = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt2}
                ]
            )
            extracted_info_new= response2.choices[0].message['content'].strip()
            print(f"THE OUTPUT IS--->{extracted_info_new}")
            logger.info(f"THE  NEW EXTRACTED OUTPUT IS------->{extracted_info_new}<--{type(extracted_info_new)}-")
            # print(f"THE KEYS IN-->"{dict(extracted_info).keys()})
            mandatory_fields = ["Name", "Location", "Type", "Prices", "RERA Number"]
            missing_fields = []

            for field in mandatory_fields:
                field_present = re.search(f'"{field}"\s*:\s*".+?"', extracted_info)
                if not field_present:
                    missing_fields.append(field)

            # if missing_fields:
            #     dispatcher.utter_message(text=f"Please provide the following missing details: {', '.join(missing_fields)}.")
            #     return []
            # elif not missing_fields:
            dispatcher.utter_message(text=f"Thanks all the info is present: {', '.join(extracted_info_new)}.")
            return [SlotSet("project_name", extracted_info)]
            # else:
            #     dispatcher.utter_message(text="Please provide a valid URL or a detailed project description.")
            #     return []
        except Exception as e:
            print (f"EXCEPTION IN OPENAI HIT---->{e}")


class ProjectForm(FormValidationAction):

    def name(self) -> str:
        return "project_form"

    async def required_slots(
        self,
        value: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
        ) ->Dict[Text, Any]:
        return ["project_name"]

    async def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        project_name = tracker.get_slot("project_name")
        dispatcher.utter_message(text=f"Received project name: {project_name}")
        return []


