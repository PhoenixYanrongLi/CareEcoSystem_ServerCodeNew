<<<<<<< HEAD:PythonServerCode/HttpServer/httpServer.py
"""
HttpServer Receives cellphone data via httpPost, as well as uploads config data to the cellphones

read_config reads a config file from a given cellID
backup_file creates an identical file with the extension .bak
write_file writes data to a path
move_file moves the temp file created by do_POST to the correct ACC/GPS location
RequestHandler provides two functions, do_POST and do_GET
do_GET uploads config data to a cellphone if a get request is received
do_POST downloads post data sent to the server from a cellphone and writes the post data to the correct path
httpServer creates the multithreaded server
"""
__author__ = "Bradley Zylstra"
__version__ = "1.0"
__maintainer__ = "Bradley Zylstra"
__email__ = "bradleybaldwin@gmx.com"
__status__ = "Development"


from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import sys
import cgi
import urlparse
import os.path
import shutil
import time

server_dir = os.path.dirname(__file__)

config_path = '/config'
#config_phone_file_path = os.path.join(server_dir, 'config.json')

upload_path = '/data'
upload_path_tmp = '/tmp'
upload_dir_tmp = os.path.join(server_dir, 'tmp')
upload_dir = os.path.join(server_dir, 'uploads')

def read_config(cellid):
    config_file_path=os.path.join(server_dir,cellid,'config.json')
    config = None
    try:
        with open(config_file_path) as config_file:
            config = config_file.read()
    except IOError:
        pass
    return config

def backup_file(filepath):
    shutil.move(filepath, filepath + '.' + str(int(time.time()*1000)) + '.bak')

def write_file(filename, file):
    if not os.path.exists(upload_dir_tmp):
        os.mkdir(upload_dir_tmp)
    filepath = os.path.join(upload_dir_tmp, filename+'.txt')
    if os.path.exists(filepath):
        backup_file(filepath)
    with open(filepath, 'wb') as output_file:
        while True:
            chunk = file.read(1024)
            if not chunk:
                break
            output_file.write(chunk)
    #move_file(filepath)


def move_file(filePath):
    fileName = os.path.basename(filePath)
    name, other = fileName.split('_', 1)
    path=os.path.join(upload_dir_tmp, name+'.txt')
    if not os.path.exists(path):
        os.mkdir(path)
    if other.find("ACC") != -1:
        path = os.path.join(path, "acc")
        if not os.path.exists(path):
            os.mkdir(path)
        shutil.move(filePath,os.path.join(path, fileName))
    elif other.find("GPS")!=-1:
        path=os.path.join(path, "gps")
        if not os.path.exists(path):
            os.mkdir(path)
        shutil.move(filePath, os.path.join(path, fileName))
    else:
        os.remove(filePath)


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse.urlparse(self.path)
        print parsed_url.path.find("config")
        print parsed_url.path.split("config\\", 1)[1]
        if parsed_url.path.find("config") == True:
            config = read_config(parsed_url.path.split("config\\", 1)[1])
            if config:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(config)
            else:
                self.send_error(500)
        elif parsed_url.path == upload_path:
            self.send_error(405)
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed_url = urlparse.urlparse(self.path)
        path = parsed_url.path
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        print self.headers
        print self.rfile
        if path == upload_path_tmp:
            if ctype=='multipart/form-data':
                form = cgi.FieldStorage(self.rfile, self.headers, environ={'REQUEST_METHOD': 'POST'})
                print form
                try:
                    fileitem = form["uploadedfile"]
                    if fileitem.file:
                        try:
                            write_file(fileitem.filename, fileitem.file)
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
        elif parsed_url.path == config_path:
            self.send_error(405)
        else:
            self.send_error(404)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def httpServer(server_ip,port):
    server_address = (server_ip, port)
    httpd = ThreadedHTTPServer(server_address, RequestHandler)

    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    print 'use <Ctrl-C> to stop'
    httpd.serve_forever()
=======
__author__ = 'Brad'
"""
HttpServer Receives cellphone data via httpPost, as well as uploads config data to the cellphones

read_config reads a config file from a given cellID
backup_file creates an identical file with the extension .bak
write_file writes data to a path
move_file moves the temp file created by do_POST to the correct ACC/GPS location
RequestHandler provides two functions, do_POST and do_GET
do_GET uploads config data to a cellphone if a get request is received
do_POST downloads post data sent to the server from a cellphone and writes the post data to the correct path
httpServer creates the multithreaded server
"""
__author__ = "Bradley Zylstra"
__version__ = "1.0"
__maintainer__ = "Bradley Zylstra"
__email__ = "bradleybaldwin@gmx.com"
__status__ = "Development"


from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import sys
import cgi
import urlparse
import os.path
import shutil
import time

server_dir = os.path.dirname(__file__)

config_path = '/config'
#config_phone_file_path = os.path.join(server_dir, 'config.json')

upload_path = '/data'
upload_dir = os.path.join(server_dir, 'uploads')

def read_config(cellid):
    config_file_path=os.path.join(server_dir,cellid,'config.json')
    config = None
    try:
        with open(config_file_path) as config_file:
            config = config_file.read()
    except IOError:
        pass
    return config

def backup_file(filepath):
    shutil.move(filepath, filepath + '.' + str(int(time.time()*1000)) + '.bak')

def write_file(filename, file):
    if not os.path.exists(upload_dir):
        os.mkdir(upload_dir)
    filepath = os.path.join(upload_dir, filename)
    if os.path.exists(filepath):
        backup_file(filepath)
    with open(filepath, 'wb') as output_file:
        while True:
            chunk = file.read(1024)
            if not chunk:
                break
            output_file.write(chunk)
    move_file(filepath)


def move_file(filePath):
    fileName = os.path.basename(filePath)
    name, other = fileName.split('_', 1)
    path=os.path.join(upload_dir,name)
    if not os.path.exists(path):
        os.mkdir(path)
    if other.find("ACC") != -1:
        path = os.path.join(path, "acc")
        if not os.path.exists(path):
            os.mkdir(path)
        shutil.move(filePath,os.path.join(path, fileName))
    elif other.find("GPS")!=-1:
        path=os.path.join(path, "gps")
        if not os.path.exists(path):
            os.mkdir(path)
        shutil.move(filePath, os.path.join(path, fileName))
    else:
        os.remove(filePath)


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse.urlparse(self.path)
        print parsed_url.path.find("config")
        print parsed_url.path.split("config\\", 1)[1]
        if parsed_url.path.find("config") == True:
            config = read_config(parsed_url.path.split("config\\", 1)[1])
            if config:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(config)
            else:
                self.send_error(500)
        elif parsed_url.path == upload_path:
            self.send_error(405)
        else:
            self.send_error(404)

    def do_POST(self):
        parsed_url = urlparse.urlparse(self.path)
        path = parsed_url.path
        ctype, pdict = cgi.parse_header(self.headers['Content-Type'])
        print self.headers
        print self.rfile
        if path == upload_path:
            if ctype=='multipart/form-data':
                form = cgi.FieldStorage(self.rfile, self.headers, environ={'REQUEST_METHOD': 'POST'})
                print form
                try:
                    fileitem = form["uploadedfile"]
                    if fileitem.file:
                        try:
                            write_file(fileitem.filename, fileitem.file)
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
        elif parsed_url.path == config_path:
            self.send_error(405)
        else:
            self.send_error(404)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def httpServer(server_ip,port):
    server_address = (server_ip, port)
    httpd = ThreadedHTTPServer(server_address, RequestHandler)

    sa = httpd.socket.getsockname()
    print "Serving HTTP on", sa[0], "port", sa[1], "..."
    print 'use <Ctrl-C> to stop'
    httpd.serve_forever()


httpServer('localhost', 8000)
>>>>>>> 23d3589b71a88c3d92ff97379ccd28f16cca7657:PythonTools/testHttpServer.py
