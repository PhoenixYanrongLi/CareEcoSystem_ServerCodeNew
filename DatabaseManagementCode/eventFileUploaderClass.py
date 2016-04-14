import functools

__author__ = 'Julien'

import datetime
import json
import os
import traceback
from simple_salesforce                      import Salesforce
from enum                                   import Enum
from dataUploadClass                        import GenericFileUploader
from HttpServer.GCMHttpServer               import GCMPush
from threading                              import _Timer, Timer
from copy                                   import copy
from DatabaseManagementCode.databaseWrapper import TableQuery, DatabaseWrapper

""" Enumeration of the different supported events. """
EventType = Enum(
    'LB'  ,  # Low battery event
    'BOK' ,  # Battery charging
    'NW'  ,  # Patient is not wearing the watch
    'NWM' ,  # Patient is not wearing the watch on morning
    'WO'  ,  # The patient is now wearing the watch
    'PLH' ,  # Patient is leaving home
    'PIH' ,  # Patient coming back home
    'WCL' ,  # The phone/watch connection is lost for more than 1 hour
    'WCR' ,  # The phone/watch connection is restored

    'NTF' ,  # Notification fulfilled by a caregiver
    'NTRT',  # A caregiver takes responsibility of a task
    'NTRR',  # A caregiver is no longer responsible of a task
)

""" Indicates if it's a new event or an event update. """
NotificationType = Enum('TRIGGERED', 'FULFILLED', 'RESP_ADDED', 'RESP_REMOVED', 'REMINDER')

class EventStruct():
    def __init__(self, patient_id, event_type, timestamp, **args):
        self.patient_id         = patient_id
        self.event_type         = event_type
        self.timestamp          = timestamp
        self.extras             = args.get('extras'           , '')
        self.metric_value       = args.get('metric_value'     , -1)
        self.severity           = args.get('severity'         , 5)
        self.message            = args.get('message'          , '')
        self.event_id           = args.get('event_id'         , patient_id + '_' + str(event_type) + '_' + timestamp)
        self.notification_type  = args.get('notification_type', NotificationType.TRIGGERED)

class UniqueLock:
    def __init__(self):
        # Delete the lock file
        self.filename = os.path.join(os.getcwd(), 'HttpServer', 'events', '.lock')
        try:
            os.remove(self.filename)
        except OSError:  # The file doesn't exist
            pass

    def acquire(self):
        # The lock is acquired if the file is empty and if we can successfully write in it
        try:
            with open(self.filename, 'r+') as f:
                f.seek(0, os.SEEK_END)
                if f.tell() == 0:
                    f.seek(0, os.SEEK_SET)
                    f.write('locked')
                    return True
        except IOError:  # The file doesn't exist
            with open(self.filename, 'w') as f:
                f.write('locked')
                return True
        return False

class Reminder(DatabaseWrapper):
    def __init__(self, interval, callback, db, event):
        DatabaseWrapper.__init__(self, db)
        self.__callback = callback
        self.__event    = event
        self.__interval = interval
        self.__timer    = Timer(self.__interval, self.__execute)

    def __execute(self):
        self.__callback(self, self.__event)
        self.__timer = Timer(self.__interval, self.__execute)
        self.__timer.start()

    def start(self):
        self.__timer.start()

    def cancel(self):
        self.__timer.cancel()

class Reminders:
    def __init__(self, delay, callback):
        self.__reminders = {}
        self.__delay     = delay
        self.__callback  = callback

    def create_reminder(self, db, event):
        if event.event_id in self.__reminders: # Should never occur!
            print 'Error: A reminder with this id already exists!'
            return
        reminder = self.__reminders[event.event_id] = Reminder(self.__delay, self.__callback, db, event)
        reminder.start()

    def cancel_reminder(self, event):
        reminder = self.__reminders.get(event.event_id)
        if reminder is not None:
            reminder.cancel()
            del self.__reminders[event.event_id]


class Helper:
    @staticmethod
    def format_notification_triggered(event):
        return {
            'type'             : 'PN',
            'patient'          : event.patient_id,
            'event'            : str(event.notification_type),
            'notification_id'  : event.event_id,
            'notification_type': str(event.event_type),
            'extras'           : event.extras
        }

    @staticmethod
    def format_notification_update(event):
        return {
            'type'             : 'PN',
            'patient'          : event.patient_id,
            'event'            : str(event.notification_type),
            'notification_id'  : event.event_id,
            'extras'           : event.extras
        }

    @staticmethod
    def format_notification_reminder(event):
        return {
            'type'             : 'PN',
            'patient'          : event.patient_id,
            'event'            : str(event.notification_type),
            'notification_id'  : event.event_id
        }

    @staticmethod
    def notify_caregivers(db, event):
        """ Notify the caregivers of the event. """

        # Format the notification
        notification_content = EventFileUploader.notification_formatters[event.notification_type](event)

        # Get the patient username
        if not db.fetch_from_database(database_name = '_' + event.patient_id,
                                      table_name    = 'profile',
                                      to_fetch      = 'USERNAME'):
            return
        patient_username = db.fetchone()[0]

        # Retrieve the caregivers information for the ones that monitor this patient
        print '  - Querying reg_id for patient \'%s\'...' % event.patient_id
        if not db.fetch_from_database(database_name = 'config',
                                      table_name    = 'caregiverPatientPairs',
                                      where         = [['patient', event.patient_id], ['monitored', 1]],
                                      join          = [
                                          [TableQuery(database_name = 'config',
                                                      table_name    = 'caregiverProfiles',
                                                      to_fetch      = ['username', 'email', 'use_email',
                                                                       'phone_number', 'use_phone_number']),
                                           ['caregiver', 'caregiver']],
                                          [TableQuery(database_name   = 'config',
                                                      table_name      = 'senderRegId',
                                                      join_table_name = 'regId',
                                                      join_to_fetch   = 'reg_id',
                                                      to_compare      = ['reg_id', 'rowid']),
                                           ['caregiver', 'sender_id']]
                                      ]):
            return

        # Send a sms or an email to each caregivers that monitor the patient
        registration_ids = []
        for entry in db:
            caregiver_username       = entry[0]
            caregiver_email          = entry[1]
            caregiver_b_email        = entry[2]
            caregiver_phone_number   = entry[3]
            caregiver_b_phone_number = entry[4]
            registration_ids.append(entry[5])
            print '     -> Sending notification to caregiver \'%s\'...' % caregiver_username

            # Format the message to send
            msg = "\nDear " + caregiver_username + ",\n\n"
            if event.notification_type is NotificationType.REMINDER:
                msg += "Don't forget to take care of the event '" + event.message + "' for " + patient_username
            elif event.notification_type is NotificationType.FULFILLED:
                msg += "The event '" + event.message + "' has been handled for " + patient_username
            elif event.notification_type is NotificationType.TRIGGERED:
                msg += "Please be aware of '" + event.message + "' for " + patient_username
            else:
                break
            msg += "!\n\nSincerely yours,\nNestSense"

            # Send the message
            if caregiver_b_phone_number != 0:
                GenericFileUploader.send_sms(caregiver_phone_number, msg)
            elif caregiver_b_email != 0:
                GenericFileUploader.send_email(caregiver_email, event.message, msg)

        # Notify the caregivers app
        if len(registration_ids) > 0:
            gcm = GCMPush(notification_content, registration_ids)
            gcm.start()

    @staticmethod
    def notify_salesforce(db, event):
        """ Notifies the salesforce of the new event. """
        event_dict = {
            "metric"     : str(event.event_type),
            "severity"   : event.severity,
            "metricValue": event.metric_value,
            "message"    : event.message
        }

        json_dict = {
            "patientId": event.patient_id,
            "event"    : event_dict
        }

        result = EventFileUploader.sf.apexecute('FMEvent/insertEvents', method='POST', data=json_dict)

        return result

class EventFileUploader(GenericFileUploader):
    lock                = UniqueLock()
    caregiver_reminders = Reminders(3600, Helper.notify_caregivers)
    salesforce_alerts   = Reminders(3600, Helper.notify_salesforce)

    notification_formatters = {
        NotificationType.TRIGGERED    : Helper.format_notification_triggered,
        NotificationType.FULFILLED    : Helper.format_notification_update,
        NotificationType.RESP_ADDED   : Helper.format_notification_update,
        NotificationType.RESP_REMOVED : Helper.format_notification_update,
        NotificationType.REMINDER     : Helper.format_notification_reminder
    }

    sf = Salesforce(username       = 'fm-integration@careeco.uat',
                    password       = 'fmr0cks!',
                    security_token = 'vnWYJMNtLbDPL9NY97JP9tJ5',
                    sandbox        = True)

    def __init__(self, database, top_file_path):
        super(EventFileUploader, self).__init__(database, top_file_path)
        self.event_callbacks = {
            EventType.LB  : self.process_low_battery_event,
            EventType.BOK : functools.partial(self.process_fulfill_event, [EventType.LB]),
            EventType.NW  : functools.partial(self.process_generic_event,  EventType.NW , "Patient Not Wearing Watch"),
            EventType.NWM : functools.partial(self.process_generic_event,  EventType.NWM, "Patient Not Wearing Watch On Morning"),
            EventType.WO  : functools.partial(self.process_fulfill_event, [EventType.NW, EventType.NWM]),
            EventType.PLH : functools.partial(self.process_generic_event,  EventType.PLH, "Patient Leaving Home"),
            EventType.PIH : functools.partial(self.process_fulfill_event, [EventType.PLH]),
            EventType.WCL : functools.partial(self.process_generic_event,  EventType.WCL, "Watch Connection Lost"),
            EventType.WCR : functools.partial(self.process_fulfill_event, [EventType.WCL]),
            EventType.NTF : functools.partial(self.process_notification_update, NotificationType.FULFILLED),
            EventType.NTRT: functools.partial(self.process_notification_update, NotificationType.RESP_ADDED),
            EventType.NTRR: functools.partial(self.process_notification_update, NotificationType.RESP_REMOVED),
        }
        #self.init_reminders_and_alerts()

    def extract_file_data(self, file):
        try:
            return json.load(file)
        except ValueError:  # Not a JSON Object
            return None

    def process_data(self, file_data, patient_id, data_stream, data_type, timestamp):
        try:
            event_type = getattr(EventType, data_type)
        except AttributeError:
            print('Unsupported event file format: ' + data_type)
            return False

        # Make sure that the event and eventStatus tables exist
        database_name       = '_' + patient_id
        events_column_names = ['id', 'metric', 'metric_value', 'severity', 'message', 'uploaded']
        status_column_names = ['id', 'timestamp', 'status', 'extras']
        if not self.create_table(
                database_name = database_name,
                table_name    = 'events',
                column_names  = events_column_names,
                column_types  = ['VARCHAR(100)', 'VARCHAR(20)', 'FLOAT', 'INT', 'VARCHAR(100)', 'BOOLEAN']
        ) or not self.create_table(database_name = database_name,
                                   table_name    = 'eventStatus',
                                   column_names  = status_column_names,
                                   column_types  = ['VARCHAR(100)', 'VARCHAR(100)', 'VARCHAR(10)', 'VARCHAR(100)']):
            print('Failed to create events tables!')
            return False

        # Parse the event
        event = self.event_callbacks[event_type](file_data, patient_id, data_stream, timestamp)
        if event is None:
            if event_type == EventType.BOK \
                    or event_type == EventType.WO \
                    or event_type == EventType.PIH \
                    or event_type == EventType.WCR:
                return True  # Simply means that the event was already fulfilled
            print('Failed to process event %s!' % event_type)
            return False

        # Save the event
        event = self.save_event(event)

        # Notify the caregiver and the salesforce
        if event.notification_type is NotificationType.TRIGGERED or event.notification_type is NotificationType.REMINDER:
            if event.event_type is EventType.LB: # Just notify low battery events for the moment
                try:
                    Helper.notify_caregivers(self, event)
                    Helper.notify_salesforce(self, event)
                except Exception as e:
                    print '\n************************* Notification Error *************************\n\n' \
                          '   - Patient id: %s\n' \
                          '   - Timestamp : %s\n' \
                          '   - Event type: %s\n' \
                          '   - Event id  : %s\n' \
                          '   - Error     : %s\n' \
                          '\nTraceback (most recent call last):\n%s' \
                          '\n**********************************************************************\n' % \
                          (event.patient_id, event.timestamp, event.event_type, event.event_id, str(e.args),
                           ''.join(traceback.format_stack()[:]))

        # Update the reminders
        #if event.event_type is EventType.LB:
        #    if event.notification_type is NotificationType.TRIGGERED:
        #        # Create timers to notify later the caregivers and the salesforce
        #        reminder = copy(event)
        #        reminder.notification_type = NotificationType.REMINDER
        #        EventFileUploader.caregiver_reminders.create_reminder(self, reminder)
        #        EventFileUploader.salesforce_alerts.create_reminder(self, reminder)
        #    elif event.notification_type is NotificationType.FULFILLED:
        #        # Cancel the corresponding timers
        #        EventFileUploader.caregiver_reminders.cancel_reminder(event)
        #        EventFileUploader.salesforce_alerts.cancel_reminder(event)

        return True

    def init_reminders_and_alerts(self):
        # Try to get the lock
        if not EventFileUploader.lock.acquire():
            return

        # Get the list of the patients
        if not self.fetch_from_database(database_name      = 'config',
                                        table_name         = 'caregiverPatientPairs',
                                        to_fetch           = 'patient',
                                        to_fetch_modifiers = 'DISTINCT'):
            return

        patient_rows = self.fetchall()
        for patient_row in patient_rows:
            patient_id = patient_row[0]

            # Check that the patient has already sent an event in the past
            if not self.table_exists(database_name = '_' + patient_id, table_name = 'eventStatus'):
                continue

            # Retrieve all the unfulfilled event linked to the current patient
            if self.fetch_from_database(database_name    = '_' + patient_id,
                                        table_name       = 'eventStatus',
                                        join_table_name  = 'events',
                                        to_compare       = ['id', 'id'],
                                        where            = [
                                            ['status', str(NotificationType.TRIGGERED)],
                                            ['id', 'NOT IN', TableQuery(
                                                database_name = '_' + patient_id,
                                                table_name    = 'eventStatus',
                                                where         = ['status', str(NotificationType.FULFILLED)],
                                                to_fetch      = 'id'
                                            )]],
                                        join_where       = ['metric', str(EventType.LB)],  # TODO Remove this condition once the caregiver can give feedback
                                        to_fetch         = ['id', 'extras', 'timestamp'],
                                        join_to_fetch    = ['metric', 'metric_value', 'severity', 'message']):
                for event_row in self:
                    event = EventStruct(
                        event_id          = event_row[0],
                        patient_id        = patient_id,
                        event_type        = getattr(EventType, event_row[3]),
                        timestamp         = event_row[2],
                        metric_value      = event_row[4],
                        severity          = event_row[5],
                        message           = event_row[6],
                        extras            = event_row[1],
                        notification_type = NotificationType.REMINDER
                    )
                    EventFileUploader.caregiver_reminders.create_reminder(self, event)
                    EventFileUploader.salesforce_alerts.create_reminder(self, event)

    def save_event(self, event):
        """
        Saves the given event in the database.
        :return Returns the event with an updated id matching an eventual previous result
        """

        database_name       = '_' + event.patient_id
        events_table_name   = 'events'
        events_column_names = ['id', 'metric', 'metric_value', 'severity', 'message', 'uploaded']
        status_table_name   = 'eventStatus'
        status_column_names = ['id', 'timestamp', 'status', 'extras']

        # Get an eventual previous event matching the given one
        if not self.fetch_from_database(database_name    = database_name,
                                        table_name       = status_table_name,
                                        join_table_name  = events_table_name,
                                        to_compare       = ['id', 'id'],
                                        where            = [
                                            ['status', str(NotificationType.TRIGGERED)],
                                            ['id', 'NOT IN', TableQuery(
                                                database_name = database_name,
                                                table_name    = status_table_name,
                                                where         = ['status', str(NotificationType.FULFILLED)],
                                                to_fetch      = 'id'
                                            )]],
                                        join_where       = ['metric', str(event.event_type)],
                                        to_fetch         = ['id'],
                                        limit            = 1):
            return event

        row = self.fetchone()
        if row is not None:  # There is a match
            event.event_id = row[0] # Update the event id
            if event.notification_type is NotificationType.TRIGGERED: # Avoid duplicate triggers
                event.notification_type = NotificationType.REMINDER
        else:
            if event.notification_type is NotificationType.FULFILLED:
                return event # No need to save several time that the event is fulfilled

        # If the event is a new one, save it
        if event.notification_type is NotificationType.TRIGGERED:
            # Insert the new event
            data = [event.event_id, str(event.event_type), event.metric_value, event.severity, event.message, False]
            if not self.insert_into_database(database_name = database_name,
                                             table_name    = events_table_name,
                                             column_names  = events_column_names,
                                             values        = data):
                return event

        # Standardize the timestamp
        format_str       = "%Y%m%d-%H%M%S"
        time_c           = datetime.datetime.strptime(event.timestamp, format_str)
        format_to_string = "%y-%m-%dT%H:%M:%S.%f"
        formatted_time   = time_c.strftime(format_to_string)

        # Save the event status
        data = [event.event_id, formatted_time, str(event.notification_type), str(event.extras)]
        self.insert_into_database(database_name = database_name,
                                  table_name    = status_table_name,
                                  column_names  = status_column_names,
                                  values        = data)
        return event

    def process_low_battery_event(self, file_data, user_id, data_stream, timestamp):
        print '******* Debug: ' + data_stream + ' ********'
        if data_stream == 'HM':
            device = 'watch'
        else:
            device = 'phone'
        return self.process_generic_event(EventType.LB, "Low Battery Detected", file_data, user_id, data_stream,
                                          timestamp, {'CAPACITY': file_data['CAPACITY'], 'DEVICE': device})

    def process_generic_event(self, event_type, message, file_data, patient_id, data_stream, timestamp, extras=''):
        return EventStruct(
            patient_id   = patient_id,
            event_type   = event_type,
            timestamp    = timestamp,
            metric_value = -1,
            severity     = 5,
            message      = message,
            extras       = extras
        )

    def process_fulfill_event(self, triggered_events_set, file_data, user_id, data_stream, timestamp):
        for event in triggered_events_set:
            # Retrieve the corresponding unfulfilled event
            if not self.fetch_from_database(database_name    = '_' + user_id,
                                            table_name       = 'eventStatus',
                                            join_table_name  = 'events',
                                            to_compare       = ['id', 'id'],
                                            where            = [
                                                ['status', str(NotificationType.TRIGGERED)],
                                                ['id', 'NOT IN', TableQuery(
                                                    database_name = '_' + user_id,
                                                    table_name    = 'eventStatus',
                                                    where         = ['status', str(NotificationType.FULFILLED)],
                                                    to_fetch      = 'id'
                                                )]],
                                            join_where       = ['metric', str(event)],
                                            to_fetch         = ['id'],
                                            limit            = 1):
                return None

            row = self.fetchone()
            if row is None:  # No match
                continue

            # Fulfill the  event
            return EventStruct(
                patient_id        = user_id,
                event_type        = event,
                timestamp         = timestamp,
                event_id          = row[0],
                notification_type = NotificationType.FULFILLED
            )
        return None

    def process_notification_update(self, notification_type, file_data, caregiver_id, data_stream, timestamp):
        patient_id      = file_data['patient']
        notification_id = file_data['notification_id']

        # Verify that the given event correspond to a real event
        if not self.fetch_from_database(database_name    = '_' + patient_id,
                                        table_name       = 'events',
                                        where            = ['id', notification_id],
                                        to_fetch         = ['metric', 'message']):
            return None

        row = self.fetchone()
        if row is None:  # The given notification is not registered
            return None

        return EventStruct(
            patient_id        = patient_id,
            event_type        = getattr(EventType, row[0]),
            timestamp         = timestamp,
            event_id          = notification_id,
            notification_type = notification_type,
            extras            = caregiver_id,
            message           = row[1],
        )

