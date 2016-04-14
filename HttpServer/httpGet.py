import socket
import sys
import re

sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
#server_address=('192.168.1.101',5252)
server_address=('198.199.116.85',22)
print >>sys.stderr, 'starting up on %s port %s' % server_address
sock.bind(server_address)
sock.listen(1)
i=0
while True:
    # Wait for a connection
    print >>sys.stderr, 'waiting for a connection'
    connection, client_address = sock.accept()
    stringDataBuffer=''
    try:
        print >>sys.stderr, 'connection from', client_address

        # Receive the data in small chunks and retransmit it
        while True:
            data = connection.recv(96)
            print >>sys.stderr, 'received "%s"' % data
            if data:
                f=open(str(i)+'.txt','a')
                stringDataBuffer.join(data)


                # Reply as HTTP/1.1 server, saying "HTTP OK" (code 200).
                # sending all this stuff
                #connection.send(r'''HTTP/1.0 200 OK
                #Content-Type: text/plain
                #Hello, world!''')
                #connection.sendall(str(204))
            else:
                print >>sys.stderr, 'no more data from', client_address
                break

    finally:
        # Clean up the connection
        stringDataBuffer=stringDataBuffer.split('filename=')[0]
        result = re.search('"(.*)"', stringDataBuffer).group(1)

        connection.close()