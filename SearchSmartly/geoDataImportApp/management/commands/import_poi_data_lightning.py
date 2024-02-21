import os
import csv
import json
import time
import threading
import sqlite3
import xml.etree.ElementTree as ET
from queue import Queue
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Import Point of Interest data from files'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str, help='Path to file(s) to import')

    def handle(self, *args, **options):
        start_time = time.time()
        db_queue = Queue()
        main_loop_flag = threading.Event()
        file_lock = threading.Lock()    
        checkout_flag = threading.Lock()
        threads = []

        for file_path in options['files']:
            if not os.path.exists(file_path):
                print(f"File '{file_path}' does not exist. Skipping...")
                return
            file_extension = file_path.split('.')[-1]
            if file_extension not in ['csv', 'json', 'xml']:
                print(f"Unsupported file type: '{file_extension}'. Skipping...")
                return
            file_thread = threading.Thread(target=process_file, args=(file_path, file_lock, file_extension, db_queue, main_loop_flag))
            db_thread = threading.Thread(target=save_to_database, args=(db_queue, checkout_flag))
            threads.append(file_thread)
            threads.append(db_thread)
        
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        self.stdout.write(self.style.SUCCESS(f"Processing took: {time.time() - start_time}"))
        self.stdout.write(self.style.SUCCESS(f"Finished Execution"))

def process_file(file_path, file_lock, file_extension, db_queue, main_loop_flag):
    with file_lock:
        data_batch = [] * 10000
        if file_extension == 'csv':
            reader = csv.DictReader(open(file_path, encoding='utf-8'),fieldnames=["poi_id","poi_name","poi_category","poi_latitude","poi_longitude","poi_ratings"])

            for index, row in enumerate(reader, start=1):
                validated_row = validate_and_create_point(row, file_extension)
                if validated_row:
                    data_batch.append(validated_row)
                if index % 10000 == 0:
                    db_queue.put(data_batch[:])
                    data_batch.clear()

        elif file_extension == 'json':
            json_data = json.load(open(file_path, 'r', encoding='utf-8'))
            for index, row in enumerate(json_data):
                validated_row = validate_and_create_point({
                        'poi_id': row.get('id'),
                        'poi_name': row.get('name'),
                        'poi_latitude': row.get('coordinates', {}).get('latitude'),
                        'poi_longitude': row.get('coordinates', {}).get('longitude'),
                        'poi_category': row.get('category'),
                        'poi_ratings': ','.join(map(str, row.get('ratings', []))),
                        'poi_description': row.get('description', "")
                    }, file_extension)
                if validated_row:
                    data_batch.append(validated_row)
                if index % 10000 == 0:
                    db_queue.put(data_batch[:])
                    data_batch.clear()  

        elif file_extension == 'xml':
            tree = ET.parse(file_path)
            root = tree.getroot()
            for index, record in enumerate(root.findall('DATA_RECORD'), start=1):                
                validated_row = validate_and_create_point({
                    'poi_id': record.find('pid').text,
                    'poi_name': record.find('pname').text,
                    'poi_latitude': record.find('platitude').text,
                    'poi_longitude': record.find('plongitude').text,
                    'poi_category': record.find('pcategory').text,
                    'poi_ratings': record.find('pratings').text,
                    'poi_description': record.find('poi_description').text if record.find('poi_description') is not None else ""
                }, file_extension)
                if validated_row:
                    data_batch.append(validated_row)
                if index % 10000 == 0:
                    db_queue.put(data_batch[:])
                    data_batch.clear()  
        
        if len(data_batch) > 0:
            db_queue.put(data_batch[:])
            data_batch.clear()

def save_to_database(db_queue, checkout_flag):
    conn = sqlite3.connect(r".\db.sqlite3")
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA cache_size = 1000000;")
    cursor.execute("PRAGMA temp_store = MEMORY;")
    cursor.execute("""CREATE TEMPORARY TABLE IF NOT EXISTS geoDataImportApp_pointsofinterest_temp (
                poi_id INTEGER UNIQUE PRIMARY KEY, 
                poi_name VARCHAR,
                poi_latitude REAL, 
                poi_longitude REAL,
                poi_category VARCHAR, 
                poi_ratings TEXT,
                poi_description TEXT, 
                data_origin VARCHAR,
                average_rating REAL)""")

    conn.commit()
    while True:
        batch = db_queue.get()
        if batch:
            try:        
                cursor.executemany(
                    "INSERT OR IGNORE INTO geoDataImportApp_pointsofinterest_temp "
                    "(poi_id, poi_name, poi_latitude, poi_longitude, "
                    "poi_category, poi_ratings, poi_description, "
                    "data_origin, average_rating) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    batch
                )
            except Exception as e:
                print(f"Error inserting data: {e}")

        db_queue.task_done()
        if db_queue.empty():
            cursor.execute("""
                INSERT OR IGNORE INTO geoDataImportApp_pointsofinterest
                SELECT * FROM geoDataImportApp_pointsofinterest_temp;
            """)
            conn.commit()
            break

    cursor.close()
    conn.close()

def validate_and_create_point(row, data_origin):  
    try:
        poi_ratings_calc = [float(rating) for rating in row['poi_ratings'].strip('{}').split(',') if rating.strip()]

        poi_id = int(row['poi_id'])
        poi_name = row['poi_name']
        poi_latitude = float(row['poi_latitude'])
        poi_longitude = float(row['poi_longitude'])
        poi_category = row['poi_category']
        poi_ratings = row['poi_ratings']
        poi_description = row.get('poi_description', "")
        average_rating = sum(poi_ratings_calc) / len(poi_ratings_calc) if poi_ratings_calc else 0
    
        return (poi_id, poi_name, poi_latitude, poi_longitude, poi_category, poi_ratings, poi_description, data_origin, average_rating)
        
    except (TypeError, ValueError) as e:
        pass