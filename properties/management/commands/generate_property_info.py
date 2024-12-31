import requests
import json
import re
from django.core.management.base import BaseCommand
from properties.models import PropertySummary, PropertyRatingReview
from django.db import connections

class Command(BaseCommand):
    help = 'Generate summary, rating, and review for each property using Ollama model'

    def handle(self, *args, **kwargs):
        # Fetch property data from the scraper database (PostgreSQL)
        with connections['trip'].cursor() as cursor:
            cursor.execute('SELECT hotel_id, "hotelName", city_id, city_name, "positionName", price, "roomType", latitude, longitude FROM hotels')
            properties = cursor.fetchall()
            properties = properties[:2]  # Limit to 5 properties for testing (can adjust as needed)

        # Loop through properties and generate summary, rating, and review
        for hotel_id, hotelName, city_id, city_name, positionName, price, roomType, latitude, longitude in properties:
            try:
                # Generate summary
                summary = self.generate_summary(hotelName, city_name, positionName, price, roomType, latitude, longitude)
                if not summary:
                    self.stdout.write(self.style.WARNING(f"Skipping ID {hotel_id} due to invalid summary."))
                    continue

                # Update or create the summary for the property
                PropertySummary.objects.update_or_create(
                    property_id=hotel_id,
                    defaults={'summary': summary}
                )

                # Generate rating and review
                rating, review = self.generate_rating_review(hotelName, city_name, positionName)
                if not rating or not review:
                    self.stdout.write(self.style.WARNING(f"Skipping ID {hotel_id} due to invalid rating/review."))
                    continue

                # Update or create rating and review for the property
                PropertyRatingReview.objects.update_or_create(
                    property_id=hotel_id,
                    defaults={'rating': rating, 'review': review}
                )

                self.stdout.write(self.style.SUCCESS(
                    f"Property ID {hotel_id} - Summary and Rating/Review generated and saved."
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing ID {hotel_id}: {str(e)}"))

    def generate_summary(self, hotelName, city_name, positionName, price=None, roomType=None, latitude=None, longitude=None):
        prompt = f"""Write a concise summary for the hotel '{hotelName}' located in {city_name}. 
                    Nearby Location: {positionName}. 
                    Room Type: {roomType if roomType else 'N/A'}, Price: {price if price else 'N/A'}, 
                    Latitude: {latitude if latitude else 'N/A'}, Longitude: {longitude if longitude else 'N/A'}."""

        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "phi",
                    "prompt": prompt,
                    "system": "You are a hotel summary expert. Respond with a concise summary.",
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

    def generate_rating_review(self, hotelName, city_name, positionName):
        prompt = f"""Generate a rating and review 30-word for the hotel '{hotelName}' located in {city_name}. 
                    Nearby Location: {positionName}. The review should be positive and professional. Do not include unrelated examples, Question Answer or extra content."""

        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "phi",
                    "prompt": prompt,
                    "system": "You are a hotel review expert. Provide a rating and review.",
                    "stream": False
                },
                timeout=None
            )

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return None, None

            response_data = response.json()
            if 'response' not in response_data:
                self.stdout.write(self.style.WARNING("No 'response' field in API response."))
                return None, None

            text = response_data['response'].strip()

            # Simplify response into rating and review
            # Look for 'Rating: 4.5/5 stars' or '4.5 stars' style formats
            rating_match = re.search(r'(\d+(\.\d+)?)(/5| stars)?', text)
            if rating_match:
                rating = float(rating_match.group(1))  # Extract and convert to float
            else:
                self.stdout.write(self.style.WARNING(f"Invalid rating format: {text}"))
                return None, None

            # Extract the review, which should follow the rating
            review_match = re.search(r'(\d+(\.\d+)?(/5| stars)?)(.*)', text)
            if review_match:
                review = review_match.group(4).strip()
            else:
                self.stdout.write(self.style.WARNING(f"Invalid review format: {text}"))
                return None, None

            return rating, review

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Request error: {str(e)}"))
            return None, None
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"JSON decode error: {str(e)}"))
            return None, None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
            return None, None