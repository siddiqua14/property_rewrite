from django.test import TestCase
from django.test import TransactionTestCase
from django.db import connections
from unittest.mock import patch, MagicMock
from django.core.management import call_command
from io import StringIO
from properties.models import Property, PropertySummary, PropertyRatingReview, Hotel

class RewriteHotelsCommandTest(TransactionTestCase):
    databases = {'default', 'trip'}

    def setUp(self):
        super().setUp()
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
                    longitude DECIMAL,
                    description TEXT
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

        # Create initial property
        Property.objects.create(
            original_id=1,
            rewritten_title='Original Title',
            description='Original Description'
        )

    def tearDown(self):
        Property.objects.all().delete()
        with connections['trip'].cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS hotels")
        super().tearDown()

    @patch('requests.post')
    @patch('myapp.management.commands.rewrite_hotels.Command.generate_description')
    @patch('django.db.backends.postgresql.psycopg2.base.Cursor.execute')  # Mock the execute method of the database cursor
    def test_successful_rewrite(self, mock_execute, mock_generate_description, mock_post):
        """Test successful rewriting of hotel name and description"""
        new_title = 'Grand Test Hotel'
        new_description = 'Luxurious downtown hotel with stunning city views.'
        
        # Mock API responses
        mock_post.side_effect = [
            MagicMock(
                status_code=200,
                json=lambda: {'response': new_title}
            ),
            MagicMock(
                status_code=200,
                json=lambda: {'response': new_description}
            )
        ]

        # Mock generate_description method to return the new description
        mock_generate_description.return_value = new_description

        # Ensure test data exists
        Property.objects.create(
            original_id=1,
            name='Original Title',  # Adjust field name if needed
            description='Original Description',
            rewritten_title='',
        )

        # Run command
        out = StringIO()
        call_command('rewrite_hotels', stdout=out)

        # Verify that the execute method was called to update the database
        mock_execute.assert_called_with("""
            UPDATE hotels  
            SET "hotelName" = %s, description = %s  
            WHERE hotel_id = %s
        """, ['Grand Test Hotel', new_description, 1])

        # Verify updates
        updated_property = Property.objects.get(original_id=1)
        self.assertEqual(
            updated_property.rewritten_title,
            new_title,
            f"Title not updated. Current in DB: {updated_property.rewritten_title}"
        )
        self.assertIn(
            'downtown hotel',
            updated_property.description,
            f"Description not updated. Current in DB: {updated_property.description}"
        )

        # Verify the 'hotels' table has been updated with the new title and description
        with connections['trip'].cursor() as cursor:
            cursor.execute("SELECT * FROM hotels WHERE hotel_id = %s", [1])
            hotel = cursor.fetchone()
            self.assertEqual(hotel[1], new_title)  # Check the updated hotelName
            self.assertEqual(hotel[9], new_description)  # Check the updated description


    @patch('requests.post')
    def test_api_failure(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=500,
            text='Internal Server Error'
        )

        out = StringIO()
        call_command('rewrite_hotels', stdout=out)

        updated_property = Property.objects.get(original_id=1)
        self.assertEqual(updated_property.rewritten_title, 'Original Title')
        self.assertIn('Ollama API error', out.getvalue())

    @patch('requests.post')
    def test_invalid_response(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {'invalid_key': 'some value'}
        )

        out = StringIO()
        call_command('rewrite_hotels', stdout=out)

        updated_property = Property.objects.get(original_id=1)
        self.assertEqual(updated_property.rewritten_title, 'Original Title')
        self.assertIn('Skipping ID 1 due to invalid rewritten title', out.getvalue())

    @patch('requests.post')
    def test_network_error(self, mock_post):
        mock_post.side_effect = Exception('Network Error')

        out = StringIO()
        call_command('rewrite_hotels', stdout=out)

        updated_property = Property.objects.get(original_id=1)
        self.assertEqual(updated_property.rewritten_title, 'Original Title')
        self.assertIn('Error generating title: Network Error', out.getvalue())

    def test_database_connection(self):
        """Test database connection and data retrieval"""
        with connections['trip'].cursor() as cursor:
            cursor.execute('SELECT hotel_id FROM hotels WHERE hotel_id = 1')
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], 1)

class GeneratePropertyContentCommandTest(TestCase):
    databases = {"default", "trip"}

    @classmethod
    def setUpTestData(cls):
        # Create the hotels table in the test database
        with connections["trip"].cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS hotels (
                    hotel_id INTEGER PRIMARY KEY,
                    "hotelName" VARCHAR(255),
                    city_id INTEGER,
                    city_name VARCHAR(255),
                    "positionName" VARCHAR(255),
                    price VARCHAR(50),
                    "roomType" VARCHAR(100),
                    latitude DECIMAL(10, 6),
                    longitude DECIMAL(10, 6)
                )
            """
            )
            # Insert test data
            cursor.execute(
                """
                INSERT INTO hotels (
                    hotel_id, "hotelName", city_id, city_name, "positionName", 
                    price, "roomType", latitude, longitude
                ) VALUES 
                (1, 'Test Hotel', 100, 'Test City', 'Downtown', '100', 'Double', 1.234, 5.678),
                (2, 'Sample Hotel', 200, 'Sample City', 'Beach', '200', 'Suite', 2.345, 6.789)
            """
            )

    def setUp(self):
        self.test_properties = [
            (
                1,
                "Test Hotel",
                100,
                "Test City",
                "Downtown",
                "100",
                "Double",
                1.234,
                5.678,
            ),
            (
                2,
                "Sample Hotel",
                200,
                "Sample City",
                "Beach",
                "200",
                "Suite",
                2.345,
                6.789,
            ),
        ]

    def tearDown(self):
        # Clean up the test database and models
        with connections["trip"].cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS hotels")
        PropertySummary.objects.all().delete()
        PropertyRatingReview.objects.all().delete()

    def mock_success_response(self, url, **kwargs):
        if "prompt" in kwargs.get("json", {}):
            if "Generate a rating and review" in kwargs["json"]["prompt"]:
                return MagicMock(
                    status_code=200,
                    json=lambda: {"response": "4.5/5 This is a test review response"},
                )
            else:
                return MagicMock(
                    status_code=200,
                    json=lambda: {"response": "This is a test summary response"},
                )

    def mock_invalid_rating_response(self, url, **kwargs):
        if "prompt" in kwargs.get("json", {}):
            if "Generate a rating and review" in kwargs["json"]["prompt"]:
                return MagicMock(
                    status_code=200,
                    json=lambda: {"response": "Invalid response without rating"},
                )
            else:
                return MagicMock(
                    status_code=200,
                    json=lambda: {"response": "This is a test summary response"},
                )

    def mock_error_response(self, url, **kwargs):
        return MagicMock(status_code=500, text="API Error")

    @patch("properties.management.commands.generate_property_info.requests.post")
    def test_command_successful_execution(self, mock_post):
        mock_post.side_effect = self.mock_success_response

        out = StringIO()
        call_command("generate_property_info", stdout=out)

        # Check that both PropertySummary and PropertyRatingReview objects were created
        self.assertEqual(PropertySummary.objects.count(), 2)
        self.assertEqual(PropertyRatingReview.objects.count(), 2)

        summary1 = PropertySummary.objects.get(property_id=1)
        self.assertTrue(len(summary1.summary) > 0)

        review1 = PropertyRatingReview.objects.get(property_id=1)
        self.assertEqual(review1.rating, 4.5)
        self.assertTrue(len(review1.review) > 0)

    @patch("properties.management.commands.generate_property_info.requests.post")
    def test_command_handles_api_error(self, mock_post):
        mock_post.side_effect = self.mock_error_response

        out = StringIO()
        call_command("generate_property_info", stdout=out)

        # Verify no objects were created due to API error
        self.assertEqual(PropertySummary.objects.count(), 0)
        self.assertEqual(PropertyRatingReview.objects.count(), 0)

    @patch("properties.management.commands.generate_property_info.requests.post")
    def test_command_handles_invalid_rating_response(self, mock_post):
        mock_post.side_effect = self.mock_invalid_rating_response

        out = StringIO()
        call_command("generate_property_info", stdout=out)

        # Verify only summaries were created, but no rating/reviews due to invalid response
        self.assertEqual(PropertySummary.objects.count(), 2)
        self.assertEqual(PropertyRatingReview.objects.count(), 0)

    def test_property_summary_str(self):
        summary = PropertySummary.objects.create(property_id=1, summary="Test summary")
        self.assertEqual(str(summary), "Summary for Property 1")

    def test_property_rating_review_str(self):
        review = PropertyRatingReview.objects.create(
            property_id=1, rating=4.5, review="Test review"
        )
        self.assertEqual(str(review), "Rating and Review for Property 1")


class PropertyModelTest(TestCase):
    
    def setUp(self):
        # Creating a Property instance
        self.property = Property.objects.create(
            original_id=1,
            original_title="Original Title",
            rewritten_title="Rewritten Title",
            description="Property description"
        )

    def test_property_str(self):
        self.assertEqual(str(self.property), "Original Title -> Rewritten Title")

    def test_property_default_values(self):
        # Test default values for existing rows
        property_obj = Property.objects.create(original_id=2)
        self.assertEqual(property_obj.original_title, "Unknown")
        self.assertEqual(property_obj.rewritten_title, "Not rewritten")
        self.assertEqual(property_obj.description, "Not rewritten")

class PropertySummaryModelTest(TestCase):

    def setUp(self):
        # Creating a PropertySummary instance
        self.property_summary = PropertySummary.objects.create(
            property_id=1,
            summary="This is a summary of the property."
        )

    def test_property_summary_str(self):
        self.assertEqual(str(self.property_summary), "Summary for Property 1")

class PropertyRatingReviewModelTest(TestCase):

    def setUp(self):
        # Creating a PropertyRatingReview instance
        self.property_rating_review = PropertyRatingReview.objects.create(
            property_id=1,
            rating=4.5,
            review="Great property with excellent services."
        )

    def test_property_rating_review_str(self):
        self.assertEqual(str(self.property_rating_review), "Rating and Review for Property 1")

    def test_property_rating_review_fields(self):
        self.assertEqual(self.property_rating_review.rating, 4.5)
        self.assertEqual(self.property_rating_review.review, "Great property with excellent services.")

class HotelModelTest(TestCase):

    def setUp(self):
        # Mock the database connection for the hotels table to avoid requiring the actual table in tests
        self.mock_hotel_data()

    @patch("django.db.backends.postgresql.base.DatabaseWrapper.connect")
    def mock_hotel_data(self, mock_connect):
        # Mocking the connection to avoid actual DB interactions
        mock_connect.return_value = True  # Simulate a successful DB connection
        
        # Simulate the creation of a Hotel object
        self.hotel = Hotel(
            hotel_id=1,
            hotelName="Sample Hotel",
            city_id=100,
            city_name="Sample City",
            positionName="Downtown",
            price=99.99,
            roomType="Single",
            latitude=40.7128,
            longitude=-74.0060,
            description="A beautiful hotel in downtown."
        )

    def test_hotel_str(self):
        self.assertEqual(self.hotel.hotelName, "Sample Hotel")

    def test_hotel_default_values(self):
        # Test default value for description
        hotel_obj = Hotel(
            hotel_id=2,
            hotelName="Another Hotel",
            city_id=200,
            city_name="Another City",
            positionName="Suburb",
        )
        self.assertEqual(hotel_obj.description, None)

    @patch("properties.models.Hotel.using_trip_db")
    def test_using_trip_db(self, mock_using_trip_db):
        # Mock the `using_trip_db` method to simulate DB interaction
        mock_using_trip_db.return_value = True  # Simulate a successful DB call
        hotels = Hotel.using_trip_db().all()
        self.assertTrue(hotels) 
