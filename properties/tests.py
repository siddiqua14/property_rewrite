from django.test import TestCase
from django.db import connections
from unittest.mock import patch, MagicMock
from django.core.management import call_command
from io import StringIO
from properties.models import Property
from django.conf import settings

class RewriteHotelsCommandTest(TestCase):
    databases = {'default', 'trip'}

    def setUp(self):
        # Create test data in the trip database
        with connections['trip'].cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS hotels")
            cursor.execute("""
                CREATE TABLE hotels (
                    hotel_id INTEGER PRIMARY KEY,
                    "hotelName" VARCHAR(255),
                    city_id INTEGER,
                    city_name VARCHAR(255),
                    "positionName" VARCHAR(255),
                    price DECIMAL,
                    "roomType" VARCHAR(255),
                    latitude DECIMAL,
                    longitude DECIMAL
                )
            """)
            cursor.execute("""
                INSERT INTO hotels (
                    hotel_id, "hotelName", city_id, city_name, 
                    "positionName", price, "roomType", latitude, longitude
                ) VALUES (
                    1, 'Original Hotel Name', 1, 'Test City', 
                    'Downtown', 199.99, 'Deluxe', 40.7128, -74.0060
                )
            """)
        
        # Create the Property instance
        self.property = Property.objects.create(
            original_id=1,
            rewritten_title='Original Title',
            description='Original Description'
        )

    def tearDown(self):
        # Clean up test data
        with connections['trip'].cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS hotels")
        Property.objects.all().delete()

    def mock_api_response(self, response_text):
        return MagicMock(
            status_code=200,
            json=lambda: {'response': response_text.strip()},
            text=response_text
        )

    @patch('requests.post')
    def test_successful_rewrite(self, mock_post):
        """Test successful rewriting of hotel title and description"""
        new_title = 'Grand Test Hotel'
        new_description = 'Luxurious downtown hotel with stunning city views.'
        
        # Mock consecutive API calls for title and description
        mock_post.side_effect = [
            self.mock_api_response(new_title),
            self.mock_api_response(new_description)
        ]

        # Run the command
        out = StringIO()
        call_command('rewrite_hotels', stdout=out)
        output = out.getvalue()
        
        # Print debug information
        print("Command output:", output)
        
        # Refresh the property instance from the database
        self.property.refresh_from_db()
        
        print("Updated title:", self.property.rewritten_title)
        print("Expected title:", new_title)

        # Verify the updates
        self.assertEqual(self.property.rewritten_title, new_title, 
                        f"Title not updated. Current: {self.property.rewritten_title}, Expected: {new_title}")
        self.assertIn('downtown hotel', self.property.description, 
                    f"Description not updated properly. Current: {self.property.description}")

    @patch('requests.post')
    def test_api_failure(self, mock_post):
        """Test handling of API failure"""
        mock_post.return_value = MagicMock(
            status_code=500,
            text='Internal Server Error'
        )

        out = StringIO()
        call_command('rewrite_hotels', stdout=out)

        # Refresh the property instance
        self.property.refresh_from_db()
        self.assertEqual(self.property.rewritten_title, 'Original Title')
        self.assertIn('Ollama API error', out.getvalue())

    @patch('requests.post')
    def test_invalid_response(self, mock_post):
        """Test handling of invalid API response"""
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'invalid_key': 'some value'}
        )

        out = StringIO()
        call_command('rewrite_hotels', stdout=out)

        # Refresh the property instance
        self.property.refresh_from_db()
        self.assertEqual(self.property.rewritten_title, 'Original Title')
        self.assertIn('Skipping ID 1 due to invalid rewritten title', out.getvalue())

    @patch('requests.post')
    def test_network_error(self, mock_post):
        """Test handling of network errors"""
        mock_post.side_effect = Exception('Network Error')

        out = StringIO()
        call_command('rewrite_hotels', stdout=out)

        # Refresh the property instance
        self.property.refresh_from_db()
        self.assertEqual(self.property.rewritten_title, 'Original Title')
        self.assertIn('Error generating title: Network Error', out.getvalue())

    def test_database_connection(self):
        """Test database connection and data retrieval"""
        with connections['trip'].cursor() as cursor:
            cursor.execute('SELECT hotel_id FROM hotels WHERE hotel_id = 1')
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], 1)

class PropertyModelTest(TestCase):
    """Test cases for Property model"""
    
    def test_property_creation(self):
        """Test creating a Property instance"""
        property_instance = Property.objects.create(
            original_id=999,
            rewritten_title='Test Property',
            description='Test Description'
        )
        self.assertEqual(Property.objects.count(), 1)
        self.assertEqual(property_instance.rewritten_title, 'Test Property')