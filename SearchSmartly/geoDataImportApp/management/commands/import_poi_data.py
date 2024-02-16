from collections import defaultdict
import csv
import os
import json
from unittest import skipIf
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from geoDataImportApp.models import CsvPointOfInterest, JsonPointOfInterest, XmlPointOfInterest
from django.core.exceptions import ValidationError
from concurrent.futures import ThreadPoolExecutor
import time
import subprocess
import pandas as pd

class Command(BaseCommand):
    help = 'Import Point of Interest data from files'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str, help='Path to file(s) to import')
        parser.add_argument('--fast', action='store_true', help='Use fast C++ implementation')

    def handle(self, *args, **options):
        use_cpp = options['fast']
        start_time = time.time()
        for file_path in options['files']:
            with open(file_path, 'r', encoding='utf-8') as file:
                file_extension = file_path.split('.')[-1]
                if file_extension == 'csv':
                    if use_cpp:
                        pass
                        validate_csv(file_path)
                        print(f"CSV took: {time.time() - start_time}")

                    else:
                        for file_path in options['files']:
                            reader = csv.DictReader(file)
                            batch = []
                            invalid_rows = []
                            with ThreadPoolExecutor() as executor:
                                futures = []
                                for i, row in enumerate(reader):
                                    futures.append(executor.submit(validate_and_create_csv_point, row, i))
                                for future in futures:
                                    try:
                                        result = future.result()
                                        if result:
                                            batch.append(result)
                                    except ValidationError as e:
                                        invalid_rows.append(e)
                            if batch:
                                CsvPointOfInterest.objects.bulk_create(batch)
                            for error in invalid_rows:
                                self.stdout.write(self.style.WARNING(error))
                elif file_extension == 'json':
                    # Handle JSON files
                    json_data = json.load(file)
                    for item in json_data:
                        poi_id = item['id']
                        poi_name = item['name']
                        poi_latitude = item['coordinates']['latitude']
                        poi_longitude = item['coordinates']['longitude']
                        poi_category = item['category']
                        poi_ratings = ','.join(map(str, item['ratings']))
                        poi_description = item.get('description', '')
                        # Create JsonPointOfInterest instance and save it
                        JsonPointOfInterest.objects.create(
                            poi_id=poi_id,
                            poi_name=poi_name,
                            poi_latitude=poi_latitude,
                            poi_longitude=poi_longitude,
                            poi_category=poi_category,
                            poi_ratings=poi_ratings,
                            poi_description=poi_description
                        )
                elif file_extension == 'xml':
                    # Handle XML files
                    tree = ET.parse(file)
                    root = tree.getroot()
                    for record in root.findall('DATA_RECORD'):
                        poi_id = record.find('pid').text
                        poi_name = record.find('pname').text
                        poi_latitude = record.find('platitude').text
                        poi_longitude = record.find('plongitude').text
                        poi_category = record.find('pcategory').text
                        poi_ratings = record.find('pratings').text
                        # Create XmlPointOfInterest instance and save it
                        XmlPointOfInterest.objects.create(
                            poi_id=poi_id,
                            poi_name=poi_name,
                            poi_latitude=poi_latitude,
                            poi_longitude=poi_longitude,
                            poi_category=poi_category,
                            poi_ratings=poi_ratings
                        )
                else:
                    self.stdout.write(self.style.WARNING(f'Unsupported file format: {file_path}'))


def validate_and_create_csv_point(row, row_number):
    """
    Validate CSV data before creating CsvPointOfInterest instance.
    """
    poi_id = row.get('poi_id')
    poi_name = row.get('poi_name')
    poi_latitude = row.get('poi_latitude')
    poi_longitude = row.get('poi_longitude')
    poi_category = row.get('poi_category')
    poi_ratings = row.get('poi_ratings')

    errors = []

    if not poi_id:
        errors.append('poi_id')
    if not poi_name:
        errors.append('poi_name')
    if not poi_latitude:
        errors.append('poi_latitude')
    if not poi_longitude:
        errors.append('poi_longitude')
    if not poi_category:
        errors.append('poi_category')
    if not poi_ratings:
        errors.append('poi_ratings')

    if errors:
        raise ValidationError(f'Missing required fields in row {row_number}: {", ".join(errors)}')

    try:
        int(poi_id)
        str(poi_name)
        float(poi_latitude)
        float(poi_longitude)
        str(poi_category)
        str(poi_ratings)
    except (TypeError, ValueError) as e:
        raise ValidationError(f'Invalid data format in row {row_number}: {e}')

    return CsvPointOfInterest(
        poi_id=poi_id,
        poi_name=poi_name,
        poi_latitude=poi_latitude,
        poi_longitude=poi_longitude,
        poi_category=poi_category,
        poi_ratings=poi_ratings
    )

def validate_csv(file_path):
    # Path to the compiled C++ program
    cpp_program_path = os.environ["FASTCSVCHECKER"]

    # Call the compiled C++ program with input file path as argument
    result = subprocess.run([cpp_program_path, file_path], capture_output=True, text=True)

    # Check the result
    if result.returncode == 0:
        print("Data validation completed successfully.")
        print(result.stdout)
    else:
        print("Error occurred during data validation.")
        print(result.stderr)
