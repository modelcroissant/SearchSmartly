# PoI Data Importer

Welcome to the PoI Data Importer Django project! This project is built to streamline the process of importing Point of Interest (PoI) data from diverse file formats (CSV, JSON, XML) into a local database. Additionally, it provides a user-friendly web interface for browsing and searching through the imported data.

The primary goal of this project is to optimise the speed and efficiency of processing data and adding it to the database. While this implementation serves as a proof of concept, it can be adapted for production use with the WSGI server. However, it's important to note that the multi-threading functionality requires thorough testing before deployment.

Efficient data processing is a key focus of this project, ensuring smooth execution even with large datasets. By employing asynchronous I/O operations for database writes and file reads, this project maximises performance and minimises processing delays.

## Caveats and Considerations

### Unit Tests:
While unit tests are fundamental to ensuring the reliability and maintainability of software projects, they weren't prioritised during the initial development phase. This decision was made to focus on rapidly prototyping and delivering core functionalities, aiming to meet project deadlines and demonstrate proof of concept. 

### Error Logging:
In the interest of streamlining development and avoiding unnecessary overhead, extensive error logging wasn't implemented during the initial stages of the project. Instead, the focus was on building and refining core features to meet project objectives efficiently.

### Internal_ID
I ran out of time to implement internal id properly, it was either going to be an UUID or self incrementing DB row depending on performance.

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
*CPU used: Intel(R) Xeon(R) CPU E3-1505M v5 @ 2.80GHz, 2801 Mhz, 4 Core(s), 8 Logical Processor(s)*

| Test Type | Normal | Fast | Lightning | Total Rows Inserted |
| --------  | ------ | ---- | --------- | ------------------- |
| XML 100 rows | 0.033s | 0.010s | 0.0052s | 100 |
| JSON 1,000 rows | 0.166s | 0.033s| 0.019s | 1000 |
| CSV 1,000,000 rows | 184.979s | 27.374s | 14.458s | 999,681 |
| JSON + CSV + XML | 189.564s | 32.126s | 15.870s | 1,000,665 |

The fast version consistently outperforms the original implementation, achieving sub-30 seconds processing time for CSV data and sub-1 second processing time for XML and JSON data. These optimisations result in significantly improved efficiency and scalability for importing Point of Interest data into the database.

### Future Enhancements:

While the fast version demonstrates substantial improvements in processing speed, there are opportunities for further optimisation. Potential enhancements include utilising SQLite's BEGIN CONCURRENT mode for asynchronous database writes, exploring alternative database engines for improved concurrency, and optimising file processing algorithms for even faster data extraction.

This code could also benefit from refactoring to adopt an object-oriented programming (OOP) approach, enhancing its modularity and setting a foundation for improved extensibility and future development. By restructuring the code into classes that encapsulate specific functionalities, such as file processing, database interaction, and data validation, we can achieve a more organised and maintainable codebase. This modular approach enables easier extension and modification of individual components, facilitating smoother integration of new features or enhancements in the future.
