from django.contrib import admin
from .models import Property, PropertySummary, PropertyRatingReview, Hotel


# Register PropertySummary model
@admin.register(PropertySummary)
class PropertySummaryAdmin(admin.ModelAdmin):
    list_display = ('property_id', 'summary')  # Fields to display
    search_fields = ('property_id',)  # Searchable fields

# Register PropertyRatingReview model
@admin.register(PropertyRatingReview)
class PropertyRatingReviewAdmin(admin.ModelAdmin):
    list_display = ('property_id', 'rating', 'review')  # Fields to display
    search_fields = ('property_id', 'rating')  # Searchable fields



@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('hotel_id', 'hotelName', 'city_name', 'positionName', 'price', 'description')
    search_fields = ('hotelName', 'city_name', 'positionName')
    list_filter = ('city_name',)

    def get_queryset(self, request):
        # Use the 'trip' database when querying for hotels
        return Hotel.using_trip_db().all()