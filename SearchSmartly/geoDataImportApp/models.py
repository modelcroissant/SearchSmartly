from enum import unique
from unittest.util import _MAX_LENGTH
from django.db import models

class PointsOfInterest(models.Model):
    poi_id = models.IntegerField(unique=True, primary_key=True)
    poi_name = models.CharField(max_length=100)
    poi_latitude = models.FloatField()
    poi_longitude = models.FloatField()
    poi_category = models.CharField(max_length=50)
    poi_ratings = models.TextField()
    poi_description = models.TextField()
    data_origin = models.CharField(max_length=5)
    average_rating = models.FloatField(default=0)