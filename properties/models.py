from django.db import models

class Property(models.Model):
    original_id = models.BigIntegerField(default=0)  # Default for existing rows
    original_title = models.TextField(default="Unknown")  # Default for existing rows
    rewritten_title = models.TextField(default="Not rewritten")  # Default for existing rows
    description = models.TextField(default="Not rewritten")  # New field for the description
    class Meta:
        db_table = 'rewrite_property_info'

    def __str__(self):
        return f"{self.original_title} -> {self.rewritten_title}"
    
class PropertySummary(models.Model):
    property_id = models.IntegerField(unique=True)  # Property ID
    summary = models.TextField()  # Summary of the property

    def __str__(self):
        return f"Summary for Property {self.property_id}"

class PropertyRatingReview(models.Model):
    property_id = models.IntegerField(unique=True)  # Property ID
    rating = models.FloatField()  # Rating for the property
    review = models.TextField()  # Review for the property

    def __str__(self):
        return f"Rating and Review for Property {self.property_id}"
class Hotel(models.Model):
    hotel_id = models.BigIntegerField(primary_key=True)
    hotelName = models.CharField(max_length=255)
    city_id = models.IntegerField()
    city_name = models.CharField(max_length=255)
    positionName = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    roomType = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)  # Newly added column

    class Meta:
        db_table = 'hotels'  # This maps to the existing hotels table in the 'trip' database
        managed = False  # Don't allow migrations to modify this table

    @classmethod
    def using_trip_db(cls):
        return cls.objects.using('trip') 