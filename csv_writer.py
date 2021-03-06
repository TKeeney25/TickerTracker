import csv
import os


class CSVWriter:
    def __init__(self, file_name, header: list, initialize=False):
        self.file_name = file_name
        self.header = header
        self.symbols = set()
        if not os.path.exists(file_name) or not self.isInCSV(self.header[0]) or initialize:
            self._initializeCSV()

    def _initializeCSV(self):
        open(self.file_name, 'w').close()
        with open(self.file_name, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(self.header)
            self.symbols.add(self.header[0])
            csv_file.flush()

    def write(self, values: list):
        with open(self.file_name, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(values)
            self.symbols.add(values[0])

    def isInCSV(self, symbol: str) -> bool:
        if len(self.symbols) == 0:
            self._populateSymbols()
        return symbol in self.symbols

    def _populateSymbols(self):
        with open(self.file_name, 'r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for row in csv_reader:
                self.symbols.add(row[0])
