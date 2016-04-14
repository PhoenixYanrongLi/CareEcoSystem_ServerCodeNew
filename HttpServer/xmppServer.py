__author__ = 'Brad'

import sleekxmpp
import multiprocessing
import logging
import json

SERVER = 'gcm.googleapis.com'
PORT = 5235
USERNAME = "890949496098@gcm.googleapis.com"
Password = "AIzaSyBIPkn-qiYm91YcZQfRyt2vWawWw2TbnBQ"
reg_id = "APA91bG6U0LQ33ENnYPBRjF1i2HprtvemRVzXXFWwOL7wF3UBXeN_VqAr1zZtQZOTV6NGdq3Wwur1DUD1SpQ6SN-53R6n2jmn_Kl_UIsDV_Ih9ItxD7yD25QospGBYlhKnf6ex8nkzXV"

class XMPPSend(sleekxmpp.ClientXMPP):
    """
    XMPPSend sends an asynchronous message to the GCM server and waits for a response
    """
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)

    def start(self, event):
        self.send_presence()
        self.get_roster()
        self.disconnect(wait=True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
    xmpp = XMPPSend(USERNAME, Password)
    if xmpp.connect(address=(SERVER,PORT), reattempt = False, use_ssl=True):
        xmpp.process(block=True)
        to_send = {'to': reg_id,
                 'message_id': 'reg_id',
                 'data': {'ma_message': 'message for android',
                          'ma_title': "Reg title"}}
        xmpp.send_raw("google", "<message><gcm xmlns='google:mobile:data'>"+json.dumps(to_send)+"</gcm></message>")
        print("Done")
    else:
        print("Unable to connect.")
