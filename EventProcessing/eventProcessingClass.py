__author__ = 'Brad'
import MySQLdb
import datetime
from simple_salesforce import Salesforce
import json
import sys


class EventProcessing:

    def __init__(self, database, database_name, username='bbzylstra@randolphcollege.edu.careeco.dev', password='moxie100', security_token='rUrhVtWfeJAcZ6Wf1S7XZml4', sandbox=True):

        self.dataB = MySQLdb.connect(host=database[0], user=database[1], passwd=database[2])
        self.cur = self.dataB.cursor()
        self.databaseName = database_name
        self.patient_id = self.databaseName[1:]
        self.length = 30*86400
        self.data = []
        self.sf = Salesforce(username=username, password=password, security_token=security_token, sandbox=sandbox)


    def set_event_length(self, length):
        """

        @param length: double(days)
        @return:true
        """
        self.length = length*86400
        return True

    def get_event_data(self, data_type, table_name):
        """
        @param data_type: str of the column selected, pass * for all data in table
        @param table_name: str of the name of the table
        @return: Double tuple of steps
        """
        current_date = self.get_current_date()
        date_from_length = current_date-self.length
        sql = 'SELECT '+data_type+' FROM '+self.databaseName+'.'+table_name+' WHERE datetime >= '+str(date_from_length)
        self.cur.execute(sql)
        event_data = self.cur.fetchall()
        if len(event_data) == 0:
            return []
        else:
            return list(zip(*event_data)[0])

    @staticmethod
    def get_current_date(self):
        """

        @return:returns the current date in seconds from the epoch
        """
        epoch = datetime.datetime.utcfromtimestamp(0)
        current_date = datetime.datetime.now()
        current_date = current_date-epoch
        current_date = current_date.total_seconds()
        return current_date

    def upload_to_sales_force(self, apex_list):

        event_dict = {
            "metric": apex_list[0],
            "severity": apex_list[1],
            "metricValue": apex_list[2],
            "message": apex_list[3]
        }

        json_dict = {
            "patientId": self.patient_id,
            "event": event_dict
        }

        result = self.sf.apexecute('FMEvent/insertEvents', method='POST', data=json_dict)

        return result

    def upload_to_database(self, event_data):
        """

        @param event_data: List of event data referenced to objnamelist
        @return:True on success
        """

        # Create event table in database if it does not yet exist
        try:
            table_string = ''
            for i in self.objnamelist:
                # Splice out __c in object names
                table_string += i[0:-3] + ' VARCHAR(255),'

            sql = "CREATE TABLE " + self.databaseName + "." + "Events (datetime DOUBLE NOT NULL,"+table_string+" PRIMARY KEY(datetime))"
            self.cur.execute(sql)

        except MySQLdb.Error:
            print "Event Table found in database: "+self.databaseName

            try:
                # Try to see if we can resize the event table

                #Get number of columns
                sql = "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema = '"+self.databaseName+"' AND table_name = 'Events' "
                self.cur.execute(sql)
                columns = int(list(self.cur.fetchall())[0][0])

                #Build list of new columns to add
                tables = ""
                if columns < len(self.objnamelist)+1:
                    for i in range(0, len(self.objnamelist)-(columns-1)):
                        tables += "ADD COLUMN "+self.objnamelist[columns+i-1][0:-3]+" VARCHAR(255),"
                    tables = tables[0:-1]

                    #add new columns to table
                    sql = "ALTER TABLE "+self.databaseName+".Events "+tables
                    self.cur.execute(sql)
                    self.dataB.commit()

            except:
                print(sys.exc_info())
                print "Select Error"

        try:
            tables_string = ''
            # add in additional %s for datetime
            s_string = '%s,'

            # Create list of tables in db and %s string for insert
            for i in self.objnamelist:
                tables_string += i[0:-3] + ','
                s_string += '%s,'

            # Remove trailing , from string
            s_string = s_string[0:-1]
            tables_string = tables_string[0:-1]

            # Create sql insert string
            sql = "INSERT INTO " + self.databaseName + "." + "Events (datetime,"+tables_string+") VALUES ("+s_string + ")"
            insert_list = event_data
            insert_list.insert(0, self.get_current_date())

            # Convert all elements to string for upload
            for i, z in enumerate(insert_list):
                insert_list[i] = str(z)

            # Upload and commit to db
            self.cur.execute(sql, tuple(insert_list))
            self.dataB.commit()
            return True

        except MySQLdb.Error:
            print 'Event insert into database '+self.databaseName+' has failed.'
            return False




objvallist = ["Stepcount", 2, 0, "Zero Stepcount"]
database = ["localhost", "brad", 'moxie100']
uploader = EventProcessing(database, '_351881065297355/11')
print uploader.upload_to_sales_force(objvallist)