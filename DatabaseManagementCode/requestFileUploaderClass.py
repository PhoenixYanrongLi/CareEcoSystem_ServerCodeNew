__author__ = 'Julien'

import json
from dataUploadClass          import GenericFileUploader
from enum                     import Enum
from HttpServer.GCMHttpServer import GCMPush

RequestType = Enum(
    'CPV',  # Caregiver profile validation
    'PA' ,  # Patient monitoring authorization (for a given caregiver)
    'CUR',  # Request to get the list of caregivers monitoring the given list of patients
    'AC' ,  # Request a caregiver account confirmation
    'FP' ,  # Ask the server to send the caregiver password by email
)


class ResponseStruct():
    def __init__(self, request_type, reg_id, data):
        self.request_type = request_type
        self.data         = data
        self.reg_id       = reg_id
        if self.reg_id is None:
            raise Exception('No registration id!')


class RequestFileUploader(GenericFileUploader):
    def __init__(self, database, top_file_path):
        super(RequestFileUploader, self).__init__(database, top_file_path)
        self.request_callbacks = {
            RequestType.CPV: self.process_caregiver_profile_validation_request,
            RequestType.PA : self.process_patient_authorization_request,
            RequestType.CUR: self.process_caregiver_username_list_request,
            RequestType.FP : self.process_password_request,
            RequestType.AC : self.process_caregiver_account_confirmation
        }

    def extract_file_data(self, file):
        try:
            return json.load(file)
        except ValueError:  # Not a JSON object
            return None

    def process_data(self, file_data, patient_id, data_stream, data_type, timestamp):
        try:
            request_type = getattr(RequestType, data_type)
        except AttributeError:
            print('Unsupported request file format: ' + data_type)
            return False

        # Parse the request
        response = self.request_callbacks[request_type](file_data, patient_id, data_stream, timestamp)
        if response is None:
            return False

        # Send the response to the sender
        self.send_response(response)

        return True

    @staticmethod
    def server_error_response(request_type, reg_id, error):
        """ Returns an invalid response containing the given server error. """
        return ResponseStruct(request_type, reg_id, {'extras': 'Server error: ' + error, 'status': 'invalid'})

    def process_caregiver_profile_validation_request(self, file_data, caregiver_id, data_stream, timestamp):
        database_name = 'config'
        table_name    = 'caregiverProfiles'
        caregiver_id  = file_data['caregiver']
        reg_id        = file_data['reg_id']

        if not self.fetch_from_database(database_name      = database_name,
                                        table_name         = 'caregiverPatientPairs',
                                        where              = ['caregiver', caregiver_id],
                                        to_fetch_modifiers = 'count'):
            return self.server_error_response(RequestType.CPV, reg_id, 'Unable to fetch from caregiver profile!')

        if self.fetchone()[0] > 0:  # The caregiver id is valid
            # Make sure the profiles table exists
            column_names = ['caregiver', 'username', 'password', 'email', 'phone_number', 'use_email',
                            'use_phone_number', 'is_admin']
            if not self.create_table(
                    database_name = database_name,
                    table_name    = table_name,
                    column_names  = column_names,
                    column_types  = ['VARCHAR(100) NOT NULL UNIQUE', 'VARCHAR(100)', 'VARCHAR(100)', 'VARCHAR(100)', \
                                     'VARCHAR(20)', 'BOOL', 'BOOL', 'BOOL DEFAULT \'0\'']
            ):
                return self.server_error_response(RequestType.CPV, reg_id, 'Unable to create caregiver profiles table!')

            # Check if the profile already exists
            if not self.fetch_from_database(database_name      = database_name,
                                            table_name         = table_name,
                                            where              = ['caregiver', caregiver_id],
                                            to_fetch_modifiers = 'count'):
                return self.server_error_response(RequestType.CPV, reg_id, 'Unable to fetch caregiver profile!')

            if self.fetchone()[0] > 0:  # A profile already exists
                return ResponseStruct(RequestType.CPV,
                                      reg_id,
                                      {
                                          'status': 'invalid',
                                          'extras': "A profile for the caregiver id '" + caregiver_id + "' already exists!"
                                      })

            # Save the registration id of the caregiver (if the sender is the caregiver phone)
            if not self.save_sender_registration_id(caregiver_id, reg_id):
                return self.server_error_response(RequestType.CPV, reg_id, 'Unable to save caregiver registration id!')

            # Save the caregiver information
            if not self.insert_into_database(database_name = database_name,
                                             table_name    = table_name,
                                             column_names  = column_names[0: -1],
                                             values        = [file_data[key] for key in column_names[0: -1]]):
                return self.server_error_response(RequestType.CPV, reg_id, 'Unable to save caregiver profile!')

            resp = { 'status': 'valid', 'is_admin': 0 }
            for tag in column_names[0: -3]:
                resp[tag] = file_data[tag]
            return ResponseStruct(RequestType.CPV, reg_id, resp)
        else:  # The caregiver id is not valid
            return ResponseStruct(RequestType.CPV, reg_id, {
                'status': 'invalid',
                'extras': "'" + caregiver_id + "' is not a valid caregiver id!"
            })

    def process_patient_authorization_request(self, file_data, caregiver_id, data_stream, timestamp):
        patient_id   = file_data['patient']
        caregiver_id = file_data['caregiver']
        reg_id       = file_data['reg_id']
        if not self.fetch_from_database(database_name      = 'config',
                                        table_name         = 'caregiverPatientPairs',
                                        where              = [['caregiver', caregiver_id], ['patient', patient_id]],
                                        to_fetch_modifiers = 'count'):
            return self.server_error_response(RequestType.PA, reg_id, 'Unable to fetch from caregiver authorizations!')

        if self.fetchone()[0] > 0:  # The caregiver can monitor the patient
            if not self.save_sender_registration_id(patient_id, reg_id):
                return self.server_error_response(RequestType.PA, reg_id, 'Unable to save patient registration id!')

            database_name  = '_' + patient_id
            profile_fields = ['USERNAME', 'TALLEST_CEILING', 'HOME_LATITUDE', 'HOME_LONGITUDE', 'START', 'END']
            if not self.table_exists(database_name, 'profile') or \
                    not self.fetch_from_database(database_name = database_name,
                                                 table_name    = 'profile',
                                                 to_fetch      = profile_fields):
                return ResponseStruct(RequestType.PA, reg_id, {
                    'status': 'valid',
                    'caregiver': caregiver_id,
                    'patient': patient_id
                })

            profile_data     = self.fetchone()
            profile          = dict([(field, profile_data[i]) for i, field in enumerate(profile_fields)])
            profile['START'] = self.UTC_to_timestamp(profile['START'])
            profile['END']   = self.UTC_to_timestamp(profile['END'])
            room_fields      = ['ROOM_NAME', 'MOTE_ID', 'FLOOR', 'CEILING_HEIGHT', 'X_DIST_FROM_PREV', 'Y_DIST_FROM_PREV', 'ROOM_IDX']

            if not self.fetch_from_database(database_name = database_name,
                                            table_name    = 'rooms',
                                            to_fetch      = room_fields):
                return ResponseStruct(RequestType.PA, reg_id, {
                    'status': 'valid',
                    'caregiver': caregiver_id,
                    'patient': patient_id
                })

            profile['ROOMS'] = [dict([(field, room_data[i]) for i, field in enumerate(room_fields)]) for room_data in self]

            return ResponseStruct(RequestType.PA, reg_id, {
                'status'   : 'valid',
                'caregiver': caregiver_id,
                'patient'  : patient_id,
                'PROFILE'  : profile
            })
        else:  # The caregiver cannot monitor the patient
            return ResponseStruct(RequestType.PA, reg_id, {
                'status': 'invalid',
                'extras': "You are not allowed to monitor the patient '" + patient_id + "'!"
            })

    def process_caregiver_username_list_request(self, file_data, caregiver_id, data_stream, timestamp):
        patient_ids = file_data['patient_ids']
        caregivers  = {}
        for patient_id in patient_ids:  # For each patient in the list
            if self.fetch_from_database(database_name    = 'config',
                                        table_name       = 'caregiverProfiles',
                                        join_table_name  = 'caregiverPatientPairs',
                                        to_compare       = ['caregiver', 'caregiver'],
                                        join_where       = ['patient', patient_id],
                                        to_fetch         = ['caregiver', 'username']):
                for row in self:  # For each caregiver monitoring the current patient
                    caregivers[row[0]] = row[1]

        caregiver_list = [{ 'id': key, 'username': value} for key, value in caregivers.iteritems()]
        return ResponseStruct(RequestType.CUR,
                              GenericFileUploader.get_sender_registration_ids(self, caregiver_id),
                              { 'caregivers': caregiver_list })

    def process_caregiver_account_confirmation(self, file_data, caregiver_id, data_stream, timestamp):
        caregiver_id = file_data['caregiver']
        password     = file_data['password']
        reg_id       = file_data['reg_id']
        patient_id   = file_data.get('patient')

        if patient_id is None:
            if not self.fetch_from_database(database_name    = 'config',
                                            table_name       = 'caregiverProfiles',
                                            where            = ['caregiver', caregiver_id],
                                            to_fetch         = ['password', 'username', 'email', 'phone_number', 'is_admin']):
                return self.server_error_response(RequestType.AC, reg_id, 'Unable to fetch caregiver profile!')
        else:
            if not self.fetch_from_database(database_name    = 'config',
                                            table_name       = 'caregiverProfiles',
                                            where            = ['caregiver', caregiver_id],
                                            join_table_name  = 'caregiverPatientPairs',
                                            to_compare       = ['caregiver', 'caregiver'],
                                            join_where       = ['patient', patient_id],
                                            to_fetch         = ['password', 'username', 'email', 'phone_number', 'is_admin']):
                return self.server_error_response(RequestType.AC, reg_id, 'Unable to fetch caregiver profile!')

        row = self.fetchone()
        if row is None:  # Invalid caregiver id
            return ResponseStruct(RequestType.AC,
                                  reg_id,
                                  {
                                      'status': 'invalid',
                                      'extras': "'" + caregiver_id + "' is not a valid caregiver id!"
                                  })

        if password != row[0]:  # Invalid password
            return ResponseStruct(RequestType.AC,
                                  reg_id,
                                  {
                                      'status': 'invalid',
                                      'extras': "Invalid password!"
                                  })

        # The provided information are valid, save the caregiver registration id ad send the answer
        if not self.save_sender_registration_id(caregiver_id, reg_id):
            return self.server_error_response(RequestType.AC, reg_id, 'Unable to save caregiver registration id!')

        resp = {'status'      : 'valid',
                'caregiver'   : caregiver_id,
                'username'    : row[1],
                'email'       : row[2],
                'phone_number': row[3],
                'is_admin'    : row[4]}
        if patient_id is not None:
            resp['patient'] = patient_id
        return ResponseStruct(RequestType.AC, reg_id, resp)

    def process_password_request(self, file_data, caregiver_id, data_stream, timestamp):
        caregiver_id = file_data['caregiver']
        reg_id       = file_data['reg_id']

        if not self.fetch_from_database(database_name    = 'config',
                                        table_name       = 'caregiverProfiles',
                                        where            = ['caregiver', caregiver_id],
                                        to_fetch         = ['email', 'username', 'password', 'use_email']):
            return self.server_error_response(RequestType.AC, reg_id, 'Unable to fetch caregiver profile!')

        row = self.fetchone()
        if row is None:  # Invalid caregiver id
            return ResponseStruct(RequestType.FP,
                                  reg_id,
                                  {
                                      'status': 'invalid',
                                      'extras': "'" + caregiver_id + "' is not a valid caregiver id!"
                                  })

        if not row[3]:  # We are not allowed to use the email address
            return ResponseStruct(RequestType.FP,
                                  reg_id,
                                  {
                                      'status': 'invalid',
                                      'extras': "We are not allowed to send you an email. Please contact a responsible!"
                                  })

        GenericFileUploader.send_email(row[0], 'Password Request',
                                       "Dear " + row[1] + ",\n\nYour password is: " + row[2] + \
                                       "\n\nBest regards,\nNestSense")

        return ResponseStruct(RequestType.FP,
                              file_data['reg_id'],
                              { 'status': 'valid' })

    def send_response(self, response):
        """ Sends the request response to the caregiver. """
        response.data['type'] = str(response.request_type)
        gcm = GCMPush(response.data, response.reg_id)
        gcm.start()
