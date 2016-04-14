__author__ = 'Brad'
import signal
import multiprocessing


variable_true = True
import signal
class SignalHandler(object):
    def __init__(self):
        self.retval = True
    def handle(self, sig, frm):
        self.retval = False

s = SignalHandler()
s.retval
signal.signal(signal.SIGINT, s.handle)
while s.retval:
    print "hello"

print "Stopped"
