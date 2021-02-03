import socket
import sys

# 1. Create a TCP connection
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = int(sys.argv[1])

# 2. Bind socket to port.
sock.bind(("", port))

# 3. Listen to all addresses.
sock.listen(port)

# 4. Repeatedly:
while True:
    # Accept new packet
    connection, client_address = sock.accept()
    # GET encoded
    get_encoded = str.encode('GET')
    data = connection.recv(4096)
    data_string = data.split()
    data_encoded_index = data_string.index(get_encoded) + 1
    request_data = str(data_string[data_encoded_index].decode())[1:]
    filename = request_data[0:request_data.find('.')]
    file_type = request_data[request_data.find('.'):]
    if file_type == '.htm' or file_type == '.html':
        try:
            file = open(request_data)

        except IOError:
            HTTP_404_Error = str.encode("HTTP/1.0 404 Not Found\r\n")
            connection.sendall(HTTP_404_Error)
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
            # connection.sendall(body)
            
    else:
        HTTP_403_Error = str.encode("HTTP/1.0 403 Forbidden\r\n")
        connection.send(HTTP_403_Error)
