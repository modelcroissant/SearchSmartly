from django.contrib import admin
from .models import PointsOfInterest

@admin.register(PointsOfInterest)
class CsvPointOfInterestAdmin(admin.ModelAdmin):
    list_display = ['poi_id', 'poi_name', 'poi_category', 'poi_ratings', 'poi_latitude', 'poi_longitude', 'data_origin', 'poi_description']