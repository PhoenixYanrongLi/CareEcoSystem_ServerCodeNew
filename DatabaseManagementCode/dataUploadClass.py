__author__ = 'Brad, Julien'

import abc
import multiprocessing
import datetime
import MySQLdb
import signal
import time
import smtplib
from os                               import path, listdir, remove
from databaseWrapper                  import DatabaseWrapper
from FileManagementCode.signalHandler import SignalHandler
from twilio.rest                      import TwilioRestClient
from email.mime.text                  import MIMEText


class GenericFileUploader(multiprocessing.Process, DatabaseWrapper):
    def __init__(self, database, top_file_path):
        multiprocessing.Process.__init__(self)
        DatabaseWrapper.__init__(self, database)
        self.cell_id_names  = []
        self.top_file_path  = top_file_path
        self.stream_name    = ''
        self.data_type_name = ''
        self.uploader_type  = path.basename(top_file_path)

    def create_phone_database(self, cell_id_name):
        """
        Creates the patient id database
        @param cell_id_name: string of the phone's cell_id
        @return: True on Completion
        """
        if not self.fetch_from_database(database_name      = 'config',
                                        table_name         = 'caregiverPatientPairs',
                                        where              = ['patient', cell_id_name],
                                        to_fetch_modifiers = 'count',
                                        limit              = 1):
            return False
        if self.fetchone()[0] == 0:
            return False
        return self.create_database('_' + cell_id_name)

    def get_dt_string(self, date_string):
        date_string = date_string.split("_", 2)[1]
        date = datetime.datetime.strptime(date_string, "%Y%m%d-%H%M%S")
        return date

    def extract_id_info(self, file_name):
        """
        Split the filename into 5 parts, patient ID name, Date string, data stream type, data type, and counter
        :param file_name: name of the file being uploaded
        :return: patientID, data_stream, data_type
        """
        count = file_name.count("_")

        names = file_name.split('_', count)
        if count > 4:
            names[3] = names[3] + '_' + names[4]
        return names[0], names[1], names[2], names[3]

    @abc.abstractmethod
    def extract_file_data(self, file):
        """
        Parses the given file and returns the corresponding data.
        :param file: The file to read
        :return Returns the file data.
        """
        return

    @abc.abstractmethod
    def process_data(self, file_data, patient_id, data_stream, data_type, time_stamp):
        """
        Process the given data. It can be database upload or any other kind of processing
        :return Returns if data has been successfully processed
        """
        return

    def update_registration_id(self, old_id, new_id):
        """
        Update the registration ids.
        :param old_id: If empty, add the new id in the database
        :param new_id: If empty, remove the old id from the database
        :return Returns if the operation is successful
        """

        # Make sure the table exist
        database_name = 'config'
        table_name    = 'regId'
        column_names  = ['rowid', 'reg_id']
        if not self.create_table(
                database_name = database_name,
                table_name    = table_name,
                column_names  = column_names,
                column_types  = ['INTEGER PRIMARY KEY AUTO_INCREMENT', 'VARCHAR(300) NOT NULL UNIQUE']
        ):
            return False

        empty_old = old_id is None or old_id == ''
        empty_new = new_id is None or new_id == ''

        if not empty_new and not empty_old: # Update the database
            if not self.fetch_from_database(database_name      = database_name,
                                            table_name         = table_name,
                                            where              = [column_names[1], old_id],
                                            to_fetch_modifiers = 'count'):
                return False

            if self.fetchone()[0] > 0:  # The old value is in the database
                return self.update_database(database_name = database_name,
                                            table_name    = table_name,
                                            to_update     = [column_names[1], new_id],
                                            where         = [column_names[1], old_id])
            else:
                return self.insert_into_database(database_name = database_name,
                                                 table_name    = table_name,
                                                 column_names  = column_names[1],
                                                 values        = new_id)

        if not empty_new:  # Insert the new value
            return self.insert_into_database(database_name = database_name,
                                             table_name    = table_name,
                                             column_names  = column_names[1],
                                             values        = new_id)

        if not empty_old:  # Remove the old value
            return self.delete_from_database(database_name = database_name,
                                             table_name    = table_name,
                                             where         = [column_names[1],  old_id])

        return False

    def save_sender_registration_id(self, sender_id, reg_id):
        """
        Save the given pair sender/registration id in the database.
        :return Returns if the operation is successful
        """
        # Make sure the registration id is in the database
        if not self.update_registration_id(None, reg_id):
            return False

        # Make sure that the table exists
        database_name = 'config'
        table_name    = 'senderRegId'
        if not self.create_table(database_name = database_name,
                                 table_name    = table_name,
                                 column_names  = ['sender_id', 'reg_id'],
                                 column_types  = ['VARCHAR(100)', 'INT']):
            return False

        # Get the registration id entry id
        if not self.fetch_from_database(database_name = database_name,
                                        table_name    = 'regId',
                                        where         = ['reg_id', reg_id],
                                        to_fetch      = 'rowid'):
            return False
        rowid = self.fetchone()[0]

        # Check if the pair sender/registration id is already in the database
        if not self.fetch_from_database(database_name      = database_name,
                                        table_name         = table_name,
                                        where              = [['sender_id', sender_id], ['reg_id', rowid]],
                                        to_fetch_modifiers = 'count'):
            return False

        if self.fetchone()[0] == 0:  # Not in the database
            return self.insert_into_database(database_name = database_name,
                                             table_name    = table_name,
                                             column_names  = ['sender_id', 'reg_id'],
                                             values        = [sender_id, rowid])
        return True

    def get_patients_list(self):
        if not self.fetch_from_database(database_name      = 'config',
                                        table_name         = 'caregiverPatientPairs',
                                        to_fetch           = 'patient',
                                        to_fetch_modifiers = 'DISTINCT'):
            return []
        return [row[0] for row in self]

    @staticmethod
    def get_sender_registration_ids(db, sender_id):
        """ Returns the list of the registration ids linked to the given sender. """

        if not db.fetch_from_database(database_name    = 'config',
                                      table_name       = 'regId',
                                      join_table_name  = 'senderRegId',
                                      to_compare       = ['rowid', 'reg_id'],
                                      join_where       = ['sender_id', sender_id],
                                      to_fetch         = 'reg_id'):
            return []
        return [row[0] for row in db]

    @staticmethod
    def timestamp_to_UTC(timestamp):
        """ Converts the given timestamp to UTC in ms. """

        format_str = "%y-%m-%dT%H:%M:%S.%f"
        time_c     = datetime.datetime.strptime(timestamp, format_str)
        epoch      = datetime.datetime.utcfromtimestamp(0)
        delta      = time_c-epoch

        return long(delta.total_seconds() * 1000)

    @staticmethod
    def UTC_to_timestamp(utc):
        seconds = float(utc)/1000
        date = datetime.datetime.utcfromtimestamp(seconds)
        return date.strftime("%y-%m-%dT%H:%M:%S.%f")

    @staticmethod
    def send_sms(phone_number, content):
        ACCOUNT_SID = "AC6e85d16080728f3d0b9047c695b7c5c4"
        AUTH_TOKEN  = "76f7f82b34a9a3fff5142a69daf5923d"

        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(
	        to    = phone_number,
	        from_ = "+12817176295",
	        body  = content
        )

    @staticmethod
    def send_email(email, subject, content):
        msg = MIMEText(content, 'plain')
        msg['Subject'] = subject
        msg['From']    = 'nestsense-2224@pages.plusgoogle.com'
        msg['To']      = email

        s = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10)
        s.set_debuglevel(1)
        try:
            s.login('nestsense.2015', 'alzheimer')
            s.sendmail(msg['From'], [ email ], msg.as_string())
        finally:
            s.quit()

    def run(self):
        s = SignalHandler()
        signal.signal(signal.SIGINT, s.handle)
        while s.stop_value:

            # Loop through all the files in the top path
            for cell_id in listdir(self.top_file_path):
                if cell_id.find('.') != 0:
                    mid_level_path = path.join(self.top_file_path, cell_id)
                    # Run if new cell id is detected
                    if cell_id not in self.cell_id_names:
                        self.create_phone_database(cell_id)
                        self.cell_id_names.append(cell_id)

                    # Loop through each data stream
                    for data_stream in listdir(mid_level_path):
                        if data_stream.find('.') < 0:
                            self.stream_name = data_stream
                            data_stream_path = path.join(mid_level_path, data_stream)

                            # Loop through each data type
                            for data_type in listdir(data_stream_path):
                                if data_type.find('.') < 0 and data_type != 'LOG':
                                    file_uploader_path  = path.join(data_stream_path, data_type)
                                    self.data_type_name = data_type

                                    #File processing below here
                                    for file_name in listdir(file_uploader_path):
                                        full_file_path = path.join(file_uploader_path, file_name)
                                        with open(full_file_path, 'r') as file:
                                            print 'Opening file_name: ' + file_name
                                            patient_id, time_stamp, stream_name, data_type = self.extract_id_info(file_name)
                                            file_data = self.extract_file_data(file)
                                            if self.process_data(file_data, patient_id, stream_name, data_type, time_stamp):
                                                remove(full_file_path)
                                                print '   - File successfully processed!'
                                            else:
                                                print '   - Failed to process file!'
                        # Check for new folders/files every 5 seconds to reduce server lag
            time.sleep(5)
        print('Received shutdown command PID: ' + str(multiprocessing.current_process()))
        return True

