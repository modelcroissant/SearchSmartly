# PoI Data Importer

This Django project is designed to import Point of Interest (PoI) data from various file formats (CSV, JSON, XML) into a local database and provide a web interface to browse and search the imported data.
The main focus of my submission is on speed of processing and adding data to the DB as efficiently as possible. This is definitely a proof of concept approach. This could be implemented into production with WSGI but multi threading will require extensive testing before release.
This code also avoids python's GIL lock as two out of three components of this code is I/O based operations, DB write and file read which works well for non-blocking when executing data processing on the CPU.

## Installation

1. Clone this repository:
This is built on Python 3.11.8
```
git clone https://github.com/modelcroissant/SearchSmartly
```

2. Install dependencies using pip (prerequisit, installed and activated venv):
this file is located at root level ./SearchSmartly/
```
pip install -r requirements.txt
```

3. Apply database migrations:
   
manage.py is located in ./SearchSmartly/SearchSmartly
```
cd SearchSmartly
python manage.py migrate
```

## Usage

### Importing PoI Data

To import PoI data from files, use the following management command:

```
python manage.py import_poi_data <file1-path> <file2-path> ...
```

Replace `<file1-path>`, `<file2-path>`, etc. with the paths to the files containing PoI data. You can specify multiple file paths separated by spaces.

### Accessing Admin Interface

1. Run the Django development server:

```
python manage.py runserver
```

2. Access the admin interface in your web browser:

```
http://localhost:8080/admin
```

3. Log in with your superuser account credentials.

4. Browse and search PoI data using the provided admin interface.

### Searching and Filtering

You can search for PoI data by internal ID or external ID using the search bar in the admin interface. Additionally, you can filter PoI data by category using the provided filter options.

## Bonus
I have included an optimised version of the original function named "import_poi_data_fast", this is a highly optimised version of the 2 hour code task which took significantly longer than 2 hours. 
I wanted to see if there is a fast implementation of the original task using pure python with minimal usage of any external libraries to reduce as much overhead as possible.
This version achieves on average sub 30 seconds for processing and saving data to DB for million rows and sub 1 second for XML and JSON data.
### Comparison
*All tests conducted on an empty DB*
| Test Type | Normal | Fast | Total Rows Inserted |
| --------  | ------ | ---- | ------------------- |
| JSON 1,000 rows | 0.166 | 0.033| 1000 |
| XML 100 rows | 0.033 | 0.010 | 100 |
| CSV 1,000,000 rows | 184.979 | 27.374 | 999,681 |
| JSON + CSV + XML | 189.564 | 32.126 | 1,000,665 |

I believe it would be possible to achieve sub 10 seconds with further optimisation like SQLite BEGIN CONCURRENT to have multiple writers write to the DB asynchronously in WAL mode into a temp table in memory, or use PostgreSQL which allows multiple concurrent write transactions. I also believe there maybe time gains in extracting the data from files by utilising more threads and batches for the I/O process or extract and process data in C or C++ (as can be seen by my .cpp attempt).
