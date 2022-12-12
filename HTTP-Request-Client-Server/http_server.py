import socket
import sys

# Socket Creation
clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Assign pocket to a port
# Parse up the url and create socket
url = sys.argv[1]
url_index = url.find('.com')
hostname = url[0:url_index+4]
path = url[url_index+4:]
port_index = url.find(':')

# Might not be necessary V
if path == '':
    path = '/'
else:
    path = path
if port_index == -1:
    port = 80
else:
    port = url[port_index:]

server_addr = (hostname, port)

sys.stderr.write('starting up on "%s" port "%s"\n' % server_addr)
clientsock.bind(server_addr)

# listen
clientsock.listen(1)

while True:
    # Establish TCP connection setup
    sys.stderr.write('Establishing connection\n')
    connection, client_addr = clientsock.accept()
    try:
        sys.stderr.write('connection from "%s"\n' % client_addr)

        # Receive and transmit data.
        while True:
            data = connection.recv(4096)
            sys.stderr.write('received "%s"\n' % data)
            if data:
                sys.stderr.write('sending data back to the client\n')
                connection.sendall(data)
            else:
                sys.stderr.write('no more data from "%s"\n', client_addr)
                break
    finally:
        # Close out the connection
        connection.close()
