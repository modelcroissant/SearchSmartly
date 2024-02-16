#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <chrono>
#include <cstdlib>

enum DataType { INTEGER, FLOAT, STRING };

struct ColumnInfo {
    std::string name;
    DataType type;
    int maxLength;
};

struct ValidationError {
    int lineNumber;
    std::string errorDescription;
    std::string rowData;
};

const std::vector<ColumnInfo> columns = {
    {"poi_id", INTEGER},
    {"poi_name", STRING, 100},
    {"poi_category", STRING, 50},
    {"poi_latitude", FLOAT},
    {"poi_longitude", FLOAT},
    {"poi_ratings", STRING, 75}
};

bool validateValue(const std::string& value, const ColumnInfo& column) {
    if (value.empty()) {
        return false; // Missing value
    }

    if (column.type == INTEGER) {
        char* endptr;
        strtol(value.c_str(), &endptr, 10);
        if (*endptr != '\0') {
            return false; // Invalid integer
        }
    }
    else if (column.type == FLOAT) {
        char* endptr;
        strtof(value.c_str(), &endptr);
        if (*endptr != '\0') {
            return false; // Invalid float
        }
    }
    else if (column.type == STRING) {
        if (value.length() > column.maxLength) {
            return false; // Exceeds maximum length
        }
    }

    return true;
}
bool validateCSV(const std::string& filename, std::vector<ValidationError>& errors) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open file " << filename << std::endl;
        return false;
    }

    std::string line;
    int lineNumber = 0;

    while (std::getline(file, line)) {
        ++lineNumber;
        if (lineNumber == 1) {
            continue;
        }

        // Extract poi_ratings value
        std::string ratings;
        try {
            size_t ratingsStart = line.find_last_of('{');
            ratings = line.substr(ratingsStart);
            line.erase(ratingsStart);
        }
        catch (const std::exception& e) {
            // If extraction fails, append the error message with a note about broken/missing rating
            errors.push_back({ lineNumber, "Broken/missing poi_ratings - " + std::string(e.what()), line });
            continue; // Move to the next line
        }

        // Process other columns
        std::stringstream ss(line);
        std::string cell;
        int cellCount = 0;
        bool validRow = true;
        std::string rowData = line;
        bool inQuotes = false;
        std::string quotedCell;
        while (std::getline(ss, cell, ',')) {
            if (!inQuotes) {
                if (!cell.empty() && cell.front() == '"') {
                    inQuotes = true;
                    quotedCell = cell;
                    continue;
                }
                ++cellCount;
            }
            else {
                if (!cell.empty()) {
                    quotedCell += "," + cell;
                    if (cell.back() == '"') {
                        inQuotes = false;
                        cell = quotedCell;
                    }
                    else {
                        continue;
                    }
                }
                else {
                    errors.push_back({ lineNumber, "Invalid cell format - Empty string found within quoted cell", rowData });
                    validRow = false;
                    break;
                }
            }

            if (cellCount > columns.size()) {
                errors.push_back({ lineNumber, "Extra columns", rowData });
                validRow = false;
                break;
            }
            if (!validateValue(cell, columns[cellCount - 1])) {
                errors.push_back({ lineNumber, "Invalid value in column " + columns[cellCount - 1].name, rowData });
                validRow = false;
                break;
            }
        }

        if (cellCount < columns.size()) {
            errors.push_back({ lineNumber, "Missing columns", rowData });
            validRow = false;
        }

        // Validate poi_ratings
        if (!validateValue(ratings, columns.back())) {
            errors.push_back({ lineNumber, "Invalid value in column " + columns.back().name, rowData });
            validRow = false;
        }
    }

    return errors.empty();
}


int main() {
    std::string filename = "C:\\Users\\dmitr\\Downloads\\pois.csv";
    auto start = std::chrono::steady_clock::now();
    std::vector<ValidationError> errors;
    if (validateCSV(filename, errors)) {
        std::cout << "CSV is valid" << std::endl;
    }
    else {
        std::cout << "CSV is not valid" << std::endl;
        auto end = std::chrono::steady_clock::now();
        std::chrono::duration<double> elapsed_seconds = end - start;
        std::cout << "Validation took " << elapsed_seconds.count() << " seconds" << std::endl;
        std::cout << "Validation errors:" << std::endl;
        for (const auto& error : errors) {
            std::cerr << "Line " << error.lineNumber << ": " << error.errorDescription << std::endl;
            std::cerr << "Row data: " << error.rowData << std::endl;
        }
    }
    return 0;
}
