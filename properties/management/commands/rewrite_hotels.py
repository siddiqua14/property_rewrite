import requests
import json
import re
from django.core.management.base import BaseCommand
from django.db import connections

class Command(BaseCommand):
    help = 'Rewrite title and add description in the hotels table using Ollama model'

    def handle(self, *args, **kwargs):
        # Ensure 'description' column exists in the 'hotels' table
        self.ensure_description_column()

        # Fetch property data from the scraper database (PostgreSQL)
        with connections['trip'].cursor() as cursor:
            cursor.execute('SELECT hotel_id, "hotelName", city_id, city_name, "positionName", price, "roomType", latitude, longitude FROM hotels')
            properties = cursor.fetchall()
            properties = properties[:2]  # Limit to 5 properties for testing (can adjust as needed)

        # Loop through properties and rewrite title and description
        for hotel_id, hotelName, city_id, city_name, positionName, price, roomType, latitude, longitude in properties:
            try:
                # Generate rewritten title
                rewritten_title = self.generate_title(hotelName, city_name, positionName)
                if not rewritten_title:
                    self.stdout.write(self.style.WARNING(f"Skipping ID {hotel_id} due to invalid rewritten title."))
                    continue

                # Generate rewritten description
                description = self.generate_description(city_name, rewritten_title, positionName, price, roomType, latitude, longitude)
                if not description:
                    self.stdout.write(self.style.WARNING(f"Skipping ID {hotel_id} due to invalid description."))
                    continue

                # Update the 'hotels' table with the new title and description
                with connections['trip'].cursor() as cursor:
                    cursor.execute("""
                        UPDATE hotels 
                        SET "hotelName" = %s, description = %s 
                        WHERE hotel_id = %s
                    """, [rewritten_title, description, hotel_id])

                self.stdout.write(self.style.SUCCESS(
                    f"Updated: Original ID {hotel_id}, Rewritten Title: {rewritten_title}, Description: {description}"
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing ID {hotel_id}: {str(e)}"))

    def ensure_description_column(self):
        with connections['trip'].cursor() as cursor:
            try:
                # Attempt to add the 'description' column if it doesn't exist
                cursor.execute("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_name = 'hotels'
                              AND column_name = 'description'
                        ) THEN
                            ALTER TABLE hotels ADD COLUMN description TEXT;
                        END IF;
                    END $$;
                """)
                self.stdout.write(self.style.SUCCESS("Verified or added 'description' column in the 'hotels' table."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error ensuring 'description' column: {str(e)}"))

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
                    "system": "You are a hotel branding expert. Respond only with the new hotel name, no additional details.",
                    "stream": False
                },
                timeout=None
            )

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return None

            response_data = response.json()
            return response_data.get('response', '').strip().split('\n')[0]  # Use only the first line

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating title: {str(e)}"))
            return None

    def generate_description(self, city_name, rewritten_title, positionName, price=None, roomType=None, latitude=None, longitude=None):
        prompt = f"""Write a concise, 20-word description for the hotel '{rewritten_title}' in {city_name}, near {positionName}.
        Include key details like amenities, price, and location. Do not include any additional explanations."""

        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "phi",
                    "prompt": prompt,
                    "system": "You are a hotel description expert. Respond only with the description text, no additional explanations.",
                    "stream": False
                },
                timeout=None
            )

            if response.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Ollama API error: {response.text}"))
                return None

            response_data = response.json()
            return response_data.get('response', '').strip().split('\n')[0]  # Use only the first line

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error generating description: {str(e)}"))
            return None
