__author__ = 'Brad'
from eventProcessingClass import EventProcessing

class stepCountEvents(EventProcessing):


    def set_step_threshold(self, delta_value):

        self.delta_value = delta_value

    def run_event_calcs(self):

        data = EventProcessing.get_event_data(self, 'steps', 'step_count')
        return data



objvallist = ['990004458126798_20150120', 125337, 'Stepcount', 0.0, 'Zero Stepcount', 1]
database = ["localhost", "brad", 'moxie100']
uploader = stepCountEvents(database, '_354796066398020')
uploader.set_step_threshold(12)
uploader.set_event_length(1)
uploader.upload_to_sales_force(objvallist)