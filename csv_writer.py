import csv


class CSVWriter:
    def __init__(self, file_name, header: list):
        self.file_path = file_name
        self._initializeCSV(header)

    def _initializeCSV(self, header: list):
        with open(self.file_path, 'w', newline='') as csv_file:
            with csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL) as csv_writer:
                csv_writer.writerow(header)

    def write(self, values: list):
        with open(self.file_path, 'a', newline='') as csv_file:
            with csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL) as csv_writer:
                csv_writer.writerow(values)
