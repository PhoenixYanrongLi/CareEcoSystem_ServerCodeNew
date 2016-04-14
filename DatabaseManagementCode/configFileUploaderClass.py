__author__ = 'Brad, Julien'

import csv
import json
import pickle
import traceback
from dataUploadClass                              import GenericFileUploader
from dataFileUploaderClass                        import DataFileUploader
from enum                                         import Enum
from HttpServer.GCMHttpServer                     import GCMPush
from InHomeMonitoringCode.training_room_estimator import TrainingRoomEstimator
from DatabaseManagementCode.databaseWrapper       import DatabaseWrapper
from DatabaseManagementCode.databaseWrapper       import Helper

ConfigType = Enum(
    'GT'     ,  # Ground trust data
    'PROFILE',  # Patient profile data
    'REGID'  ,  # Registration id change
    'CPU'    ,  # Caregiver profile update
    'PMU'    ,  # Caregiver patient monitoring update
)

class ConfigFileUploader(GenericFileUploader):
    __ERROR_THRESH = 0.2

    def __init__(self, database, top_file_path):
        super(ConfigFileUploader, self).__init__(database, top_file_path)
        self.data_extractors = {
            ConfigType.GT      : self.extract_ground_trust_data,
            ConfigType.PROFILE : self.extract_json_data,
            ConfigType.REGID   : self.extract_json_data,
            ConfigType.CPU     : self.extract_json_data,
            ConfigType.PMU     : self.extract_json_data,
        }
        self.config_processors = {
            ConfigType.GT      : self.process_ground_trust_data,
            ConfigType.PROFILE : self.process_profile_data,
            ConfigType.REGID   : self.process_registration_data,
            ConfigType.CPU     : self.process_caregiver_profile_update,
            ConfigType.PMU     : self.process_caregiver_patient_monitoring_update,
        }

    def extract_file_data(self, file):
        try:
            config_type = getattr(ConfigType, self.data_type_name)
        except AttributeError:
            print('Unsupported config file type: ' + self.data_type_name)
            return None

        return self.data_extractors[config_type](file)

    def process_data(self, file_data, patient_id, data_stream, data_type, time_stamp):
        # Check that data are valid
        if file_data is None:
            print 'Invalid data provider!'
            return False

        # Get the right processor and execute it
        try:
            config_type = getattr(ConfigType, self.data_type_name)
        except AttributeError:
            print('Unsupported config file type: ' + self.data_type_name)
            return None

        return self.config_processors[config_type](file_data, patient_id, data_stream, data_type)

    @staticmethod
    def extract_ground_trust_data(file):
        # Extract ground trust data as regular data
        reader            = csv.reader(file, delimiter=" ")
        header, reader    = DataFileUploader.extract_header_info(reader)
        file_data, reader = DataFileUploader.get_file_data(reader, header, [2, 3])
        return [header, file_data]

    @staticmethod
    def extract_json_data(file):
        try:
            return json.load(file)
        except ValueError:  # Not a JSON Object
            return None

    def process_ground_trust_data(self, file_data, patient_id, data_stream, data_type):
        # Process ground trust data as regular data
        header        = file_data[0]
        data          = file_data[1]
        database_name = '_' + patient_id
        table_name    = self.uploader_type + self.stream_name + self.data_type_name
        column_names, column_types = DataFileUploader.extract_var_types_headers(header)

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

    def parse_and_store_rooms_info(self, patient_id, tallest_ceiling_height, rooms_data):
        """
        Read the given dictionary containing the room data and store those values into the database.
        Prepare the rooms for the classifier
        :return: success (if the operation is successful), room_ids, beaconcoors: room_ids contains a list of the
        mote ids, beaconcoors is a dictionary containing the room names and the corresponding mote location.
        """
        column_names       = ['ROOM_NAME', 'MOTE_ID', 'FLOOR', 'CEILING_HEIGHT', 'X_DIST_FROM_PREV', 'Y_DIST_FROM_PREV', 'ROOM_IDX']
        database_name      = '_' + patient_id
        table_name         = 'rooms'
        beaconcoors        = {}
        room_ids           = ''
        (x, y)             = (0, 0)

        # Backup an eventual old table
        need_new_table = True
        if self.table_exists(database_name, table_name):
            # If the values are the same, no need to update the table
            if not self.fetch_from_database(database_name      = database_name,
                                            table_name         = table_name,
                                            to_fetch           = '*',
                                            to_fetch_modifiers = 'count'):
                return False, None, None, None
            if self.fetchone()[0] == len(rooms_data): # Same number of rooms
                need_new_table = False
                for room_data in rooms_data:
                    if not self.fetch_from_database(database_name      = database_name,
                                                    table_name         = table_name,
                                                    to_fetch           = '*',
                                                    to_fetch_modifiers = 'count',
                                                    where              = [[key, room_data[key]] for key in column_names]):
                        return False, None, None, None
                    if self.fetchone()[0] == 0: # One of the rooms is different
                        need_new_table = True
                        break

            if need_new_table:
                backup_name = Helper.format_backup_table_name(table_name)
                self.rename_table(database_name, table_name, backup_name)

        # Save rooms
        if need_new_table:
            if not self.create_table(
                    database_name = database_name,
                    table_name    = table_name,
                    column_names  = column_names,
                    column_types  = ['VARCHAR(100)', 'VARCHAR(100) PRIMARY KEY', 'INT', 'FLOAT', 'FLOAT', 'FLOAT', 'INT']
            ):
                return False, None, None

            for room_data in rooms_data:
                if not self.insert_into_database(database_name = database_name,
                                                 table_name    = table_name,
                                                 column_names  = column_names,
                                                 values        = [room_data[key] for key in column_names]):
                    return False, None, None

        # Extract room's data
        for room_data in rooms_data:
            data                 = [room_data[key] for key in column_names]
            x                   += data[4]
            y                   += data[5]
            z                    = data[2] * tallest_ceiling_height + data[3]
            beaconcoors[data[0]] = (x, y, z)
            room_ids            += data[1] + ','

        return True, room_ids[0: -1], beaconcoors

    def parse_and_store_patient_info(self, patient_id, patient_data, reg_id):
        """
        Read the given dictionary containing the patient data and those information for the training
        :return: success (if the operation is successful), beaconcoors, start_timestamp, end_timestamp:
        See parse_and_store_rooms_info() for beaconcoors, start_timestamp and end_timestamp indicate
        the period of data to use for training.
        """
        column_names    = ['USERNAME', 'TALLEST_CEILING', 'HOME_LATITUDE', 'HOME_LONGITUDE', 'START', 'END', 'VALID',
                           'clf', 'trainer']
        database_name   = '_' + patient_id
        table_name      = 'profile'
        data            = [patient_data[key] for key in column_names[0: -3]]
        data[4]         = self.timestamp_to_UTC(data[4])
        data[5]         = self.timestamp_to_UTC(data[5])
        data.append(0)

        # Process rooms
        success, room_ids, beaconcoors = self.parse_and_store_rooms_info(patient_id, data[1], patient_data['ROOMS'])
        if not success:
            return False, None, None, None

        # Save the registration id
        if not self.save_sender_registration_id(patient_id, reg_id):
            return False, None, None, None

        # Backup an eventual old table
        need_new_table = True
        if self.table_exists(database_name, table_name):
            # If the values are the same, no need to update the table
            if not self.fetch_from_database(database_name      = database_name,
                                            table_name         = table_name,
                                            to_fetch           = column_names[0:-3]):
                return False, None, None, None

            need_new_table = False
            for v1, v2 in zip(self.fetchone(), data[0:-1]): # For some reason a conditional fetch doesn't work...
                if isinstance(v1, basestring) or isinstance(v2, basestring):
                    v1 = str(v1)
                    v2 = str(v2)
                if v1 != v2:
                    need_new_table = True
                    backup_name    = Helper.format_backup_table_name(table_name)
                    self.rename_table(database_name, table_name, backup_name)
                    break

        # Create a new profile table
        if need_new_table:
            if not self.create_table(
                    database_name = database_name,
                    table_name    = table_name,
                    column_names  = column_names,
                    column_types  = ['VARCHAR(100)', 'FLOAT', 'FLOAT', 'FLOAT', 'VARCHAR(100)', 'VARCHAR(100)',
                                     'BOOLEAN DEFAULT FALSE', 'LONGBLOB', 'LONGBLOB']
            ):
                return False, None, None, None

            # Save the profile
            if not self.insert_into_database(database_name = database_name,
                                             table_name    = table_name,
                                             column_names  = column_names[0: -2],
                                             values        = data):
                return False, None, None, None

        return True, beaconcoors, data[4], data[5]

    def train_house_monitoring(self, patient_id, beaconcoors, start_timestamp, end_timestamp):
        """
        Train the classifier.
        :return: Returns if the operation is successful and the classifier error. Above 10%, it's a failure
        """

        # Retrieve the ground trust entries
        database_name = '_' + patient_id
        if not self.fetch_from_database(database_name = database_name,
                                        table_name    = 'configMMGT',
                                        where         = [['type' , 'CR'],
                                                         ['start', '>=', start_timestamp],
                                                         ['end'  , '<=', end_timestamp]],
                                        order_by      = ['start', 'ASC']):
            return False, 0
        traingtlist = [[row[1], row[2], row[3]] for row in self]  # [[label, start, end], ...]

        # Retrieve the rssi entries
        if not self.fetch_from_database(database_name = database_name,
                                        table_name    = 'dataHMRSSI',
                                        where         = [['timestamp', '>=', start_timestamp],
                                                         ['timestamp', '<=', end_timestamp]],
                                        order_by      = ['timestamp', 'ASC']):
            return False, 0
        trainrssilist = [[row[i] for i in range(0, 2 + 2 * row[1])] for row in self]

        # Train the classifier
        trainer      = TrainingRoomEstimator(beaconcoors)
        clf, sumdict = trainer.train_classifier(trainrssilist, traingtlist)
        error        = sumdict["classifier error"]

        # Store the classifier and the trainer
        clf     = pickle.dumps(clf)
        trainer = pickle.dumps(trainer)
        if error <= ConfigFileUploader.__ERROR_THRESH:
            valid = 1
        else:
            valid = 0
        if not self.update_database(database_name = database_name,
                                    table_name    = 'profile',
                                    to_update     = [['clf', clf], ['trainer', trainer], ['VALID', valid]]):
            return False, 0

        return True, error

    @staticmethod
    def notify_user(is_valid, reg_id, error):
        """ Notify the user of the success or not of the training. """
        content = { 'type': 'PPV' }
        if is_valid:
            content['status'] = 'valid'
        else:
            content['status'] = 'invalid'
            content['extras'] = error

        gcm = GCMPush(content, reg_id)
        gcm.start()

    def process_profile_data(self, file_data, patient_id, data_stream, data_type):
        """ Process the given patient's profile. Stores it, trains a classifier and notify the user of the result. """

        # Process the patient's information
        reg_id = file_data['reg_id']
        success, beaconcoors, start, end = self.parse_and_store_patient_info(patient_id, file_data, reg_id)
        if not success:
            self.notify_user(False, reg_id, 'Failed to parse and save patient information!')
            return True

        # Train the classifier and notify the user
        try:
            print '***** Training starts *****'
            success, error = self.train_house_monitoring(patient_id, beaconcoors, start, end)
            if not success:
                self.notify_user(False, reg_id, 'Failed to train room classifier!')
            else:
                self.notify_user(error <= ConfigFileUploader.__ERROR_THRESH, reg_id,
                                 'Failed to properly train the room classifier (The error %f is too high).\n'
                                 'Please verify your setup and try again.' % error)
            print '***** Training ends (Error: %f) *****' % error
        except Exception as e:
            print '***** Training failed *****'
            traceback.print_exc(e)

            error = ''
            for err in e.args:
                error += str(err) + '\n'
            self.notify_user(False, reg_id, error[0: -1])

        return True

    def process_registration_data(self, file_data, user_id, data_stream, data_type):
        """ Update the given registration id. """
        if 'old_id' in file_data:
            return self.update_registration_id(file_data['old_id'], file_data['new_id'])
        return self.update_registration_id(None, file_data['new_id'])

    def process_caregiver_profile_update(self, file_data, caregiver_id, data_stream, data_type):
        """ Update the caregiver profile. """
        column_names = ['username', 'password', 'email']
        return self.update_database(database_name = 'config',
                                    table_name    = 'caregiverProfiles',
                                    to_update     = [[name, file_data[name]] for name in column_names],
                                    where         = ['caregiver', caregiver_id])

    def process_caregiver_patient_monitoring_update(self, file_data, caregiver_id, data_stream, data_type):
        """ Update the caregiver profile. """
        monitored = False
        if file_data['monitored'] == 'true':
            monitored = True

        return self.update_database(database_name = 'config',
                                    table_name    = 'caregiverPatientPairs',
                                    to_update     = ['monitored', monitored],
                                    where         = [['caregiver', caregiver_id], ['patient', file_data['patient']]])

