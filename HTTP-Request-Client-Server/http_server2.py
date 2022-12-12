import socket
import sys
import select
import queue

# 1. Create a TCP connection
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setblocking(0)
port = int(sys.argv[1])

# 2. Bind socket to port.
sock.bind(("", port))

# 3. Listen to all addresses.
sock.listen(port)

# 4. Initialize list of open connections, among other things
open_connections = []
outputs = []
message_queues = {}

# 5. Repeatedly:

# Make a list of sockets we are waiting to hear from.
open_connections.append(sock)

# add accept socket to read list, call select

while open_connections:
    # call select, wait for at least one socket to be ready for processing
    #print(open_connections)
    readable, writable, exceptional = select.select(open_connections, [], [])
    # Look through readable sockets.
    for socks in readable:
        # If socket in readable is the original, look for accept sockets and add them to read list.
        if socks is sock:
            connection, client_address = socks.accept()
            connection.setblocking(0)
            open_connections.append(connection)
            # print('  connection from:', client_address, file=sys.stderr)
            # Project wants us to repeat 4b-4f in Part 2.
        else:
            # print('      closing', client_address, file=sys.stderr)
            connection.settimeout(1)
            data = socks.recv(1024)
            get_encoded = str.encode('GET')
            # Ignores request that is blank or doesn't have GET
            if get_encoded not in data or data == '':
                break
            data_string = data.split()
            data_encoded_index = data_string.index(get_encoded) + 1
            request_data = str(data_string[data_encoded_index].decode())[1:]
            filename = request_data[0:request_data.find('.')]
            file_type = request_data[request_data.find('.'):]
            # print('    recieved {!r} from {}'.format(data.decode(), socks.getpeername()), file=sys.stderr)
            if data:
                if file_type == '.htm' or file_type == '.html':
                    try:
                        file = open(request_data)

                    except IOError:
                        HTTP_404_Error = str.encode("HTTP/1.0 404 Not Found\r\n")
                        connection.sendall(HTTP_404_Error)
                        open_connections.remove(connection)
                    finally:
                        file = open(request_data)
                        body = str.encode(file.read())
                        HTTP_200_OK = "HTTP/1.0 200 OK\r\n" \
                                      "Content-Length: {}\r\n" \
                                      "Content-Type: text/html\r\n\r\n".format(len(body.decode()))
                        HTTP_200_OK = str.encode(HTTP_200_OK)
                        file.close()
                        response = HTTP_200_OK + body
                        connection.sendall(response)
                        connection.close()
                        open_connections.remove(connection)

                        # connection.sendall(body)
                else:
                    HTTP_403_Error = str.encode("HTTP/1.0 403 Forbidden\r\n")
                    connection.send(HTTP_403_Error)
                    open_connections.remove(connection)
            else:
                open_connections.remove(connection)


