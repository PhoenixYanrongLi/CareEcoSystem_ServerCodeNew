__author__ = 'Brad'

import unittest
from EventProcessing.eventProcessingClass import EventProcessing
class EventTester(unittest.TestCase):

    def setUp(self):
        self.objvallist = ["Stepcount", 2, 0, "Zero Stepcount"]
        self.database = ["localhost", "brad", 'moxie100']
        self.uploader = EventProcessing(self.database, '_351881065297355/11')
    def testDatabaseUpload(self):


    def testSalesforceUpload(self):
        self.uploader.upload_to_sales_force(self.objvallist)
