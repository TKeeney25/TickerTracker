import csv


class CSVWriter:
    def __init__(self, file_name, header: list):
        self.file_name = file_name
        self._initializeCSV(header)

    def _initializeCSV(self, header: list):
        with open(self.file_name, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header)

    def write(self, values: list):
        with open(self.file_name, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(values)
