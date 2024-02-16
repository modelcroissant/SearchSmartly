import csv
import json
import time
import threading
import xml.etree.ElementTree as ET
from queue import Queue
from django.core.management.base import BaseCommand
from geoDataImportApp.models import PointsOfInterest
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Import Point of Interest data from files'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str, help='Path to file(s) to import')

    def handle(self, *args, **options):
        start_time = time.time()
        db_queue = Queue()
        main_loop_flag = threading.Event() 
        db_thread = threading.Thread(target=save_to_database, args=(db_queue, main_loop_flag))
        db_thread.start()
        file_lock = threading.Lock()
        for file_path in options['files']:
            threading.Thread(target=process_file, args=(file_path, db_queue, file_lock)).start()

        main_loop_flag.wait()
        print(f"Processing took: {time.time() - start_time}")

def process_file(file_path, db_queue, file_lock):
    with file_lock:
        file_extension = file_path.split('.')[-1]
        batch_size = 50000
        batch = []
        with open(file_path, 'r', encoding='utf-8') as file:
            if file_extension == 'csv':
                reader = csv.DictReader(file)
                data_origin = "csv"
                for index, row in enumerate(reader):
                    data = validate_and_create_point({
                        'poi_id': row.get('poi_id'),
                        'poi_name': row.get('poi_name'),
                        'poi_latitude': row.get('poi_latitude'),
                        'poi_longitude': row.get('poi_longitude'),
                        'poi_category': row.get('poi_category'),
                        'poi_ratings': row.get('poi_ratings'),
                        'poi_description': ""
                    }, index, data_origin)
                    if data:
                        batch.append(data)
                    if len(batch) >= batch_size:
                        db_queue.put(batch[:])
                        batch.clear()

            elif file_extension == 'json':
                json_data = json.load(file)
                data_origin = "json"
                for index, item in enumerate(json_data):
                    data = validate_and_create_point({
                        'poi_id': item.get('id'),
                        'poi_name': item.get('name'),
                        'poi_latitude': item.get('coordinates', {}).get('latitude'),
                        'poi_longitude': item.get('coordinates', {}).get('longitude'),
                        'poi_category': item.get('category'),
                        'poi_ratings': ','.join(map(str, item.get('ratings', []))),
                        'poi_description': item.get('description', "")
                    }, index, data_origin)
                    if data:
                        batch.append(data)
                    if len(batch) >= batch_size:
                        db_queue.put(batch[:])
                        batch.clear()

            elif file_extension == 'xml':
                tree = ET.parse(file_path)
                root = tree.getroot()
                data_origin = "xml"
                for index, record in enumerate(root.findall('DATA_RECORD')):                
                    data = validate_and_create_point({
                        'poi_id': record.find('pid').text,
                        'poi_name': record.find('pname').text,
                        'poi_latitude': record.find('platitude').text,
                        'poi_longitude': record.find('plongitude').text,
                        'poi_category': record.find('pcategory').text,
                        'poi_ratings': record.find('pratings').text,
                        'poi_description': record.find('poi_description').text if record.find('poi_description') is not None else ""
                    }, index, data_origin)
                    if data:
                        batch.append(data)
                    if len(batch) >= batch_size: 
                        db_queue.put(batch[:])
                        batch.clear()

        if batch:
            db_queue.put(batch[:])

def save_to_database(db_queue, main_loop_flag):
    ## PRO-TIP DELETE THE DB, SAVE TIME
    ##
    while True:
        batch = db_queue.get()
        if batch:
            PointsOfInterest.objects.bulk_create(batch, ignore_conflicts=True)
        db_queue.task_done()
        if db_queue.empty():
            main_loop_flag.set()
            break 


def validate_and_create_point(row, index, data_origin):
    poi_id = row.get('poi_id')
    poi_name = row.get('poi_name')
    poi_latitude = row.get('poi_latitude')
    poi_longitude = row.get('poi_longitude')
    poi_category = row.get('poi_category')
    poi_ratings = row.get('poi_ratings')
    poi_description = row.get('poi_description')
    data_origin = data_origin

    try:
        poi_id = int(poi_id)
        poi_latitude = float(poi_latitude)
        poi_longitude = float(poi_longitude)
    except (TypeError, ValueError) as e:
        print(ValidationError(f'Invalid data format on row {index}: {e}'))
        return

    if not all([poi_id, poi_name, poi_latitude, poi_longitude, poi_category, poi_ratings]):
        print(ValidationError(f'Missing required fields in row {index}'))
        return 
    
    return PointsOfInterest(
        poi_id=poi_id,
        poi_name=poi_name,
        poi_latitude=poi_latitude,
        poi_longitude=poi_longitude,
        poi_category=poi_category,
        poi_ratings=poi_ratings,
        poi_description = poi_description,
        data_origin = data_origin,
    )