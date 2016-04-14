from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import sys
import cgi
import urlparse
import os.path
import shutil
import time

server_dir = os.path.dirname(__file__)

config_phone_path = '/phoneconfig'
config_phone_file_path = os.path.join(server_dir, 'config.json')

data_path = '/data'
data_dir = os.path.join(server_dir, 'data')

events_path = '/events'
events_dir = os.path.join(server_dir, 'events')

config_path = '/config'
config_dir = os.path.join(server_dir, 'config')

requests_path = '/requests'
requests_dir = os.path.join(server_dir, 'requests')

path_dir_dict = {data_path: data_dir, events_path: events_dir, config_path: config_dir, requests_path: requests_dir}

def read_config(cellid):
    config_file_path = os.path.join(server_dir, cellid, 'config.json')
    config = None
    try:
        with open(config_file_path) as config_file:
            config = config_file.read()
    except IOError:
        pass
    return config


def backup_file(file_path):
    shutil.move(file_path, file_path + '.' + str(int(time.time()*1000)) + '.bak')


def write_file(filename, file, file_directory):
    if not os.path.exists(file_directory):
        os.mkdir(file_directory)

    # Add .txt to the filename because the uploaded files have no extension
    file_path = os.path.join(file_directory, filename+'.txt')

    # Checks if the file already exists, if it does, create a .bak file
    if os.path.exists(file_path):
        backup_file(file_path)

    # Write the file in chunks of data
    with open(file_path, 'wb') as output_file:
        while True:
            chunk = file.read(1024)
            if not chunk:
                break
            output_file.write(chunk)
    move_file(file_path, file_directory)


def move_file(file_path, file_directory):
    """
    This function creates the parallel file structure, which looks like this:
    uploads-
        -[patientIDString]
            -[data stream type(either HM or MM)]
                -[data type(etc. ACC, GPS, RSSI)]
                    -[data files are stored here]
    :param file_path: Path of the file being moved
    :return: True on completion
    """

    # Get the name of the file being moved
    file_name = os.path.basename(file_path)

    # Split the filename into 5 parts, patient ID name, Date string, data stream type, data type, and counter
    names = file_name.split('_', 4)

    # Create the top level path under uploads, this is a folder named the patient ID string
    path = os.path.join(file_directory, names[0])
    if not os.path.exists(path):
        os.mkdir(path)

    # Create the next path under the patient ID string, this is the data stream type
    upload_type_path = os.path.join(path, names[2])
    if not os.path.exists(upload_type_path):
        os.mkdir(upload_type_path)

    # Create the data type specific folder, this will be under the data stream type
    data_type_path = os.path.join(upload_type_path, names[3])
    if not os.path.exists(data_type_path):
        os.mkdir(data_type_path)
    shutil.move(file_path, os.path.join(data_type_path, file_name))

    return True


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse.urlparse(self.path)
        print parsed_url.path.find("config")
        print parsed_url.path.split("config\\", 1)[1]
        if parsed_url.path.find("config") == True:
            config = read_config(parsed_url.path.split("config\\",1)[1])
            if config:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(config)
            else:
                self.send_error(500)
        elif parsed_url.path == data_path:
            self.send_error(405)
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed_url = urlparse.urlparse(self.path)
        path = parsed_url.path
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        if path in [data_path, config_path, events_path, requests_path]:
            if ctype == 'multipart/form-data':
                form = cgi.FieldStorage(self.rfile, self.headers, environ={'REQUEST_METHOD': 'POST'})
                try:
                    fileitem = form["uploadedfile"]
                    if fileitem.file:
                        try:
                            write_file(fileitem.filename, fileitem.file, path_dir_dict[path])
                        except Exception as e:
                            print e
                            self.send_error(500)
                        else:
                            print fileitem.filename
                            self.send_response(200)
                            self.end_headers()
                            self.wfile.write("OK")
                        return
                except KeyError:
                    pass
            # Bad request
            self.send_error(400)
        elif parsed_url.path == config_phone_path:
            self.send_error(405)
        else:
            self.send_error(404)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def httpServer(server_ip, port):
    server_address = (server_ip, port)
    httpd = ThreadedHTTPServer(server_address, RequestHandler)

    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    print 'use <Ctrl-C> to stop'
    httpd.serve_forever()