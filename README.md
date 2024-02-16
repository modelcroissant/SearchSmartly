# PoI Data Importer

This Django project is designed to import Point of Interest (PoI) data from various file formats (CSV, JSON, XML) into a local database and provide a web interface to browse and search the imported data.

## Installation

1. Clone this repository:
This is built on Python 3.11.8
```
git clone [SearchSmartlyRepo](https://github.com/modelcroissant/SearchSmartly)
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

## Contributing

If you would like to contribute to this project, feel free to open an issue or submit a pull request. Contributions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
