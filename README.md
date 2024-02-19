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
Included in this project is an optimised version of the original function for processing data named "import_poi_data_fast." This version is designed to achieve significantly faster processing and insertion of data into the database compared to the original implementation.

### Key Differences:

- **Threading and Queue Usage**: The fast version utilises multiple threads and queues to parallelise the processing of data from files and the insertion into the database. Each file processing task, data validation, and database insertion operation are handled concurrently, maximizing system resources and reducing processing time.

- **Optimised File Processing**: The fast version efficiently processes files in chunks, significantly reducing memory usage and improving performance. It implements batch processing techniques tailored to each file format (CSV, JSON, XML), allowing for faster extraction and transformation of data.

- **Database Insertion Optimisation**: Instead of using Django's ORM for bulk insertion, the fast version directly interacts with the SQLite database using the sqlite3 module. It leverages SQLite's WAL mode and asynchronous processing to enhance write performance and minimise overhead.

- **Error Handling and Data Validation**: Both versions perform data validation to ensure the integrity of the imported data. However, the fast version optimises error handling and data validation processes to minimise computational overhead and maximise throughput.

### Performance Comparison:

The table below summarises the performance comparison between the original and fast versions of the data processing function:

*All tests conducted on an empty DB*
| Test Type | Normal | Fast | Total Rows Inserted |
| --------  | ------ | ---- | ------------------- |
| JSON 1,000 rows | 0.166 | 0.033| 1000 |
| XML 100 rows | 0.033 | 0.010 | 100 |
| CSV 1,000,000 rows | 184.979 | 27.374 | 999,681 |
| JSON + CSV + XML | 189.564 | 32.126 | 1,000,665 |

The fast version consistently outperforms the original implementation, achieving sub-30 seconds processing time for CSV data and sub-1 second processing time for XML and JSON data. These optimisations result in significantly improved efficiency and scalability for importing Point of Interest data into the database.

### Future Enhancements:

While the fast version demonstrates substantial improvements in processing speed, there are opportunities for further optimisation. Potential enhancements include utilising SQLite's BEGIN CONCURRENT mode for asynchronous database writes, exploring alternative database engines for improved concurrency, and optimising file processing algorithms for even faster data extraction.