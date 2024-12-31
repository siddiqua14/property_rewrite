import requests
import json
from django.core.management.base import BaseCommand
from properties.models import Property  # Import your Property model
from django.db import connections

class Command(BaseCommand):
    help = 'Rewrite hotel title using an external service and generate a description'

    def handle(self, *args, **kwargs):
        # Set up connection to 'scraper_db' database (which is Postgres DB for hotels)
        with connections['trip'].cursor() as cursor:
            cursor.execute('SELECT hotel_id, "hotelName", city_id, city_name, "positionName", price, "roomType", latitude, longitude FROM hotels')
            properties = cursor.fetchall()
            # Limit to only 3 hotels
            properties = properties[:2]

        # Loop through hotels and use external API to rewrite titles and generate descriptions
        for hotel_id, hotelName, city_id, city_name, positionName, price, roomType, latitude, longitude in properties:
            try:
                # Generate title and description
                rewritten_title = self.generate_title(hotelName, city_name, positionName)
                description = self.generate_description(city_name, hotelName, positionName, price, roomType, latitude, longitude)

                if not rewritten_title:
                    self.stdout.write(self.style.WARNING(f"Skipping ID {hotel_id} due to invalid rewritten title."))
                    continue

                if not description:
                    self.stdout.write(self.style.WARNING(f"Skipping ID {hotel_id} due to invalid description."))
                    continue

                # Replace the original hotel name with the rewritten title in the description
                description = description.replace(hotelName, rewritten_title)

                # Check if Property with the same original_id exists
                property_instance = Property.objects.filter(original_id=hotel_id).first()

                if property_instance:
                    # If the Property exists, update it
                    property_instance.rewritten_title = rewritten_title
                    property_instance.description = description
                    property_instance.save()  # Save the updated record

                    self.stdout.write(self.style.SUCCESS(
                        f"Updated: Original ID {hotel_id}\nRewritten: {rewritten_title}\nDescription: {description}\n"
                    ))
                else:
                    # If no matching Property, log or handle as needed (optional)
                    self.stdout.write(self.style.WARNING(f"No existing record for Original ID {hotel_id}. Skipping update."))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing ID {hotel_id}: {str(e)}"))

    def generate_title(self, hotelName, city_name, positionName):
        prompt = f"""Change this hotel name into something new and unique:
                    Original hotel: {hotelName}
                    City: {city_name}
                    Nearby Location: {positionName}"""

        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "phi",
                    "prompt": prompt,
                    "system": "You are a hotel branding expert. Respond only with the new hotel name without any extra descriptions or puzzle explanations.  Do not include unrelated examples, comparisons, or extra content.",
                    "stream": False
                },
                timeout=None
            )

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return None

            response_data = response.json()
            if 'response' not in response_data:
                self.stdout.write(self.style.WARNING("No 'response' field in API response."))
                return None

            text = response_data['response'].strip()

            # Remove unwanted prefixes like "New hotel name:" or similar
            unwanted_prefixes = ["New hotel name:", "TITLE:", "Rewritten:"]
            for prefix in unwanted_prefixes:
                if text.lower().startswith(prefix.lower()):
                    text = text[len(prefix):].strip()

            # Return only the hotel name, ensuring no unwanted content
            title = text.strip()

            return title

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Request error: {str(e)}"))
            return None
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON decode error: {str(e)}"))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
            return None

    def generate_description(self, city_name, hotelName, positionName, price=None, roomType=None, latitude=None, longitude=None):
        prompt = f"""Write a concise, 20-word description for the hotel '{hotelName}' in {city_name}, near {positionName}. 
                Include key details like amenities, price, and location. Do not include unrelated examples, comparisons, or extra content."""

        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "phi",
                    "prompt": prompt,
                    "system": "You are a hotel description expert. Respond with a concise, 20-word description.",
                    "stream": False
                },
                timeout=None
            )

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return None

            response_data = response.json()
            if 'response' not in response_data:
                return None

            return response_data['response'].strip()

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Request error: {str(e)}"))
            return None
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON decode error: {str(e)}"))
            return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
            return None
