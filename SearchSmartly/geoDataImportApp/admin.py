from django.contrib import admin
from .models import CsvPointOfInterest, JsonPointOfInterest, XmlPointOfInterest

@admin.register(CsvPointOfInterest)
class CsvPointOfInterestAdmin(admin.ModelAdmin):
    list_display = ['poi_id', 'poi_name', 'poi_category', 'poi_ratings']

@admin.register(JsonPointOfInterest)
class JsonPointOfInterestAdmin(admin.ModelAdmin):
    list_display = ['poi_id', 'poi_name', 'poi_category', 'poi_ratings']

@admin.register(XmlPointOfInterest)
class XmlPointOfInterestAdmin(admin.ModelAdmin):
    list_display = ['poi_id', 'poi_name', 'poi_category', 'poi_ratings']