__author__ = 'Brad, Julien'

import csv, re
from DatabaseManagementCode.dataUploadClass import GenericFileUploader

class DataFileUploader(GenericFileUploader):
    @staticmethod
    def extract_header_info(reader_ptr):
        """
        Extracts the header from the file for create_database_table as a list
        :param reader_ptr: pointer to the csv reader object
        :return:header info, reader_ptr
        """
        header = []
        header = reader_ptr.next()
        return header, reader_ptr

    @staticmethod
    def get_file_data(reader_ptr, header, timestamp_indexes=[0]):
        """
        Given a pointer to a csv reader object, loop through the data and return a double array of the data
        :param reader_ptr: csv reader object
        :return: double array of values, reader_ptr
        """
        file_data = []
        for row in reader_ptr:
            data_list = []
            var       = ''
            for index, i in enumerate(row):
                if i is None or len(i) == 0:
                    continue
                if i[0] == '[':
                    if i[-1] == ']':    # Single word: '[Something]'
                        data_list.append(i)
                    else:               # Multiple words between brackets: '[This is a long sentence]'
                        var = i + ' '
                elif len(var) > 0:       # Looking for the end of the variable
                    if i[-1] == ']':    # End of the variable
                        data_list.append(var + i)
                        var = ''
                    else:               # Still reading the variable
                        pass
                else:                   # A simple variable
                    data_list.append(i)

            if len(header) != len(data_list): # Invalid data row
                print 'Invalid data list! %s -> %s' % (str(header), str(data_list))
                continue

            for index in timestamp_indexes:
                data_list[index] = DataFileUploader.timestamp_to_UTC(data_list[index])
            file_data.append(data_list)

        return file_data, reader_ptr

    def extract_file_data(self, file):
        reader            = csv.reader(file, delimiter=" ")
        header, reader    = self.extract_header_info(reader)
        file_data, reader = self.get_file_data(reader, header)
        return [header, file_data]

    @staticmethod
    def extract_var_types_headers(header):
        """
        Extracts the variable types from the header and returns them in a list
        :param header: The header list with variable types
        :return: header, types. header is the header list sans variable type. Types are the extracted variable types in
        a list
        """
        type_lookup_dict = {"[s]": "VARCHAR(100)", "[f]": "FLOAT", "[i]": "INT", "[b]": "BOOLEAN"}
        types = []

        for colindex, column in enumerate(header):
            index = column.find("[")
            column_name = column[0:index]
            if column_name == 'timestamp':  # Special case for timestamps stored as long
                types.append('BIGINT')
            else:
                types.append(type_lookup_dict[column[index:index + 3]])
            header[colindex] = column_name

        return header, types

    def process_data(self, file_data, patient_id, data_stream, data_type, time_stamp):
        header        = file_data[0]
        data          = file_data[1]
        database_name = '_' + patient_id
        table_name    = self.uploader_type + self.stream_name + self.data_type_name
        column_names, column_types = self.extract_var_types_headers(header)

        # Make sure the table exists
        if not self.create_table(database_name = database_name,
                                 table_name    = table_name,
                                 column_names  = column_names,
                                 column_types  = column_types):
            return False

        # Insert the data into the database
        return self.insert_into_database(database_name = database_name,
                                         table_name    = table_name,
                                         column_names  = column_names,
                                         values        = data)


