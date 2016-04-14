__author__ = 'Brad'
from gcm import GCM
import multiprocessing

class GCMPush(multiprocessing.Process):
    """
    Class to syncronously http post to gcm server. Pass json data, a json string containing the data field, and the
    registration id of the phone you wish to post to.
    """
    def __init__(self, json_data, reg_id):
        super(GCMPush, self).__init__()
        self.API_KEY   = "AIzaSyBjUNo32k8XOOZVtlHuOEg4L3VwmTe-ziM"
        self.json_data = json_data
        self.gcm       = GCM(self.API_KEY)

        if isinstance(reg_id, list):
            self.reg_id = reg_id
        else:
            self.reg_id = [ reg_id ]

    def run(self):
        self.gcm.json_request(registration_ids=self.reg_id, data=self.json_data)
