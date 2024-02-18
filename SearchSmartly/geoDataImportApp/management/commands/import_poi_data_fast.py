import os
import csv
import json
import time
import threading
import sqlite3
import xml.etree.ElementTree as ET
from queue import Queue
from django.core.management.base import BaseCommand
from geoDataImportApp.models import PointsOfInterest

class Command(BaseCommand):
    # This is a highly optimised vesrion of the 2 hour code task
    # I wanted to see if there is a fast implementation of the original task using only python.
    # This version achieves on average sub 30 seconds for processing and saving data to DB for the CSV 
    # and sub 1 second for XML and JSON data

    help = 'Import Point of Interest data from files'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str, help='Path to file(s) to import')

    def handle(self, *args, **options):
        start_time = time.time()
        db_queue = Queue()
        data_queue = Queue()
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
            file_thread = threading.Thread(target=process_file, args=(file_path, file_lock, file_extension, data_queue, main_loop_flag))
            data_thread = threading.Thread(target=validate_and_create_point, args=(data_queue, db_queue, file_extension, main_loop_flag))
            db_thread = threading.Thread(target=save_to_database, args=(db_queue, checkout_flag))
            threads.append(file_thread)
            threads.append(db_thread)
            threads.append(data_thread)
        
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        main_loop_flag.set()    

        print(f"Processing took: {time.time() - start_time}")
        print("Finished execution")

def process_file(file_path, file_lock, file_extension, data_queue, main_loop_flag):
    with file_lock:
        data_batch = []
        main_loop_flag.set()

        if file_extension == 'csv':
            with open(file_path, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file, fieldnames=["poi_id","poi_name","poi_category","poi_latitude","poi_longitude","poi_ratings"])
                for index, row in enumerate(reader, start=1):
                    data_batch.append(row)
                    if index % 100000 == 0:
                        data_queue.put(data_batch[:])
                        data_batch.clear()

        elif file_extension == 'json':
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
                for index, item in enumerate(json_data, start=1):
                    data = {
                        'poi_id': item.get('id'),
                        'poi_name': item.get('name'),
                        'poi_latitude': item.get('coordinates', {}).get('latitude'),
                        'poi_longitude': item.get('coordinates', {}).get('longitude'),
                        'poi_category': item.get('category'),
                        'poi_ratings': ','.join(map(str, item.get('ratings', []))),
                        'poi_description': item.get('description', "")
                    }
                    data_batch.append(data)
                    if index % 100000 == 0:
                        data_queue.put(data_batch[:])
                        data_batch.clear()
                    

        elif file_extension == 'xml':
            tree = ET.parse(file_path)
            root = tree.getroot()
            for index, record in enumerate(root.findall('DATA_RECORD'), start=1):                
                data = {
                    'poi_id': record.find('pid').text,
                    'poi_name': record.find('pname').text,
                    'poi_latitude': record.find('platitude').text,
                    'poi_longitude': record.find('plongitude').text,
                    'poi_category': record.find('pcategory').text,
                    'poi_ratings': record.find('pratings').text,
                    'poi_description': record.find('poi_description').text if record.find('poi_description') is not None else ""
                }
                data_batch.append(data)
                if index % 100000 == 0:
                    data_queue.put(data_batch[:])
                    data_batch.clear()
        
        if len(data_batch) > 0:
            data_queue.put(data_batch[:])
            data_batch.clear()
        
        main_loop_flag.clear()

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
                values = [
                    (
                        obj.poi_id, obj.poi_name, obj.poi_latitude, obj.poi_longitude,
                        obj.poi_category, obj.poi_ratings, obj.poi_description,
                        obj.data_origin, obj.average_rating
                    )
                    for obj in batch
                ]

                # Bulk insert operation
                cursor.executemany(
                    "INSERT OR IGNORE INTO geoDataImportApp_pointsofinterest_temp "
                    "(poi_id, poi_name, poi_latitude, poi_longitude, "
                    "poi_category, poi_ratings, poi_description, "
                    "data_origin, average_rating) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    values
                )
            except Exception as e:
                print(f"Error inserting data: {e}")

        db_queue.task_done()
        if db_queue.empty():
            # When the queue is empty, transfer data from temporary table to main table
            cursor.execute("""
                INSERT OR IGNORE INTO geoDataImportApp_pointsofinterest
                SELECT * FROM geoDataImportApp_pointsofinterest_temp;
            """)
            conn.commit()
            break

    cursor.close()
    conn.close()

def validate_and_create_point(data_queue, db_queue, data_origin, main_loop_flag):
    while True:
        batch = data_queue.get()
        if batch:
            points_of_interest = []
            for row in batch:
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
                    
                    poi = PointsOfInterest(
                        poi_id=poi_id,
                        poi_name=poi_name,
                        poi_latitude=poi_latitude,
                        poi_longitude=poi_longitude,
                        poi_category=poi_category,
                        poi_ratings=poi_ratings,
                        poi_description=poi_description,
                        data_origin=data_origin,
                        average_rating=average_rating
                    )
                    
                    points_of_interest.append(poi)
                    
                except (TypeError, ValueError) as e:
                    continue
            db_queue.put(points_of_interest[:])
            points_of_interest.clear()
            data_queue.task_done()
            if data_queue.empty() and not main_loop_flag.is_set():
                break