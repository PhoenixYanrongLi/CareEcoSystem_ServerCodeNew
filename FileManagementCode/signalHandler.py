__author__ = 'Brad'


# Class to handle SIGINT to shutdown threads gracefully
class SignalHandler(object):
    def __init__(self):
        self.stop_value = True

    def handle(self, sig, frm):
        self.stop_value = False