from enum import unique
from django.db import models

class CsvPointOfInterest(models.Model):
    poi_id = models.IntegerField(unique=True)
    poi_name = models.CharField(max_length=100)
    poi_latitude = models.FloatField()
    poi_longitude = models.FloatField()
    poi_category = models.CharField(max_length=50)
    poi_ratings = models.TextField()

class JsonPointOfInterest(models.Model):
    poi_id = models.IntegerField(unique=True)
    poi_name = models.CharField(max_length=100)
    poi_latitude = models.FloatField()
    poi_longitude = models.FloatField()
    poi_category = models.CharField(max_length=50)
    poi_ratings = models.TextField()
    poi_description = models.TextField()

class XmlPointOfInterest(models.Model):
    poi_id = models.IntegerField(unique=True)
    poi_name = models.CharField(max_length=100)
    poi_latitude = models.FloatField()
    poi_longitude = models.FloatField()
    poi_category = models.CharField(max_length=50)
    poi_ratings = models.TextField()
