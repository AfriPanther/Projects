import socket
import sys
# There are some aspects of this code that are taken from the textbook,
# other Piazza linked resources, and python documentation.

# Repeat process from http_server

# Socket Creation
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Parse up the url and create socket
url = sys.argv[1]
# Ensure no https urls
if url[0:5] == 'https':
    sys.stderr.write('Error: Attempted access to Encrypted website.\n')
    sys.exit(1)
elif not url[0:4] == 'http':
    sys.stderr.write('Error: URL must begin with "http" \n')
    sys.exit(1)

url_minus_http = url[7:]
url_index = url_minus_http.find('/')

# if the slash is not found, figure out host name another way.
if url_index == -1:
    hostname = url[0:]
    url_index = len(hostname)
else:
    # difference between url and url_minus is 7. url_index starts at the suffix
    #  (.com, .org), which is 4 before the 1st
    url_index += 3
    hostname = url[0:url_index + 4]

path = url[url_index+4:]
port = url.split(':')[-1].split('/')[0]
# Check for special cases
if path == '':
    path = '/'
else:
    path = path
if port == int:
    port = port
    portflag = True
elif port == '':
    port = 80
    portflag = False
else:
    port = int(url.split(':')[-1].split('/')[0])
    portflag = True

if hostname[0:4] == 'http' and not portflag:
    hostname = hostname[7:url_index+4]
elif hostname[0:4] == 'http' and portflag:
    hostname = hostname[7:url_index-1]
else:
    hostname = hostname

server_addr = (hostname, port)

# For debugging purposes

sys.stderr.write('connection to "%s" port "%s"\n' % server_addr)
# Connect socket to server
sock.connect((hostname, port))

# Send request
# Message format received from StackOverflow
message = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(path, hostname)
# debugging purposes
# send the GET request into the pipeline!
sock.sendall(message.encode())
sys.stderr.write('sending "%s"\n' % message)

# Search for Response
answer = sock.recv(4096)
# split answer into string so we can search
answer_string = answer.split()

# encode the string 'Content-Length' for later
content_length_encoded = str.encode('Content-length:')
# Encode Location and Redirect 301 or 302
location_encoded = str.encode('Location:')

# Check for 301 or 302
Redirected = True
redirect_count = 0
while Redirected:
    if answer_string[1].decode() == '301' or answer_string[1].decode() == '302':
        Redirected = True
        redirect_count += 1
        if redirect_count == 11:
            sys.stderr.write('Error: Too Many Redirects\n')
            sys.exit(1)
        index = answer_string.index(location_encoded) + 1
        # location is the new url
        url = str(answer_string[index].decode())

        sys.stderr.write('Redirected to:' + url + '\n')

        if url[0:5] == 'https':
            sys.stderr.write('Error: Attempted access to Encrypted website.\n')
            sys.exit(1)

        url_minus_http = url[7:]
        url_index = url_minus_http.find('/')

        # if the slash is not found, figure out host name another way.
        if url_index == -1:
            hostname = url_minus_http[0:]
        else:
            # difference between url and url_minus is 7. url_index starts at the suffix
            #  (.com, .org), which is 4 before the 1st
            url_index += 3
            hostname = url[0:url_index + 4]

        path = url[url_index + 4:]
        port = url.split(':')[-1].split('/')[0]
        # Check for special cases
        if path == '':
            path = '/'
        else:
            path = path
        if port == int:
            port = port
            portflag = True
        elif port == '':
            port = 80
            portflag = False
        else:
            port = int(url.split(':')[-1].split('/')[0])
            portflag = True
        if hostname[0:4] == 'http' and not portflag:
            hostname = hostname[7:url_index + 4]
        elif hostname[0:4] == 'http' and portflag:
            hostname = hostname[7:url_index - 1]
        else:
            hostname = hostname

        server_addr = (hostname, port)

        sock.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, port))

        message = "GET {} HTTP/1.0\r\nHost: {}\r\n\r\n".format(path, hostname)
        sock.sendall(message.encode())
        sys.stderr.write('sending "%s"\n' % message)
        # New Answer
        answer = sock.recv(4096)
    # split answer into string so we can search
        answer_string = answer.split()
    else:
        Redirected = False
# define the body! This is the part we want!
# Split the answer_string into a list of each new line.
# the body is in the last index of that generated list
body = answer.decode().split("\r\n\r\n")[-1]

# Now, look for 'Content-length' in our answer string
if content_length_encoded in answer_string:
    # Find index for where "Content-Length" is.
    index = answer_string.index(content_length_encoded) + 1
    # Once found, store content_length variable
    content_length = int(answer_string[index].decode())
    # If we didn't grab enough data, figure out how many bytes are left
    bytes_left = content_length - len(body)

    # If bytes still remain, receive more data and tag it onto our answer
    while bytes_left > 0:
        # Receive more data
        answer_continued = sock.recv(4096)
        # Tag it onto our answer
        answer += answer_continued
        answer_string = answer.split()
        # Update body
        body = answer.decode().split("\r\n\r\n")[-1]
        # Look to see if there are bytes left
        bytes_left = content_length - len(body)
else:
    # if content-length is not found, then we need to keep going!
    while True:
        answer_continued = sock.recv(4096)
        # if answer_continued is 0, breaks. No more data left to retrieve.
        if not answer_continued:
            break
        # Add onto the answer and continue!
        answer += answer_continued
        answer_string = answer.split()

# Check content-type
content_type_encoded = str.encode('content-type:')

if content_type_encoded in answer_string:
    content_type_index = answer_string.index(content_type_encoded) + 1
    content_type = str(answer_string[content_type_index].decode())
    if content_type == 'text/html':
        content_type = content_type
    else:
        sys.stderr.write('Content-type incompatible. Must be text/html.\n')
        sys.exit(1)

# Print body to stdout

if answer_string[1].decode() == '200':
    sys.stdout.write(body)
    sock.close()
    sys.exit(0)
elif int(answer_string[1].decode()) >= 400:
    sys.stdout.write(body)
    sock.close()
    sys.exit(1)
else:
    sys.stdout.write(body)
    sock.close()
    sys.exit(1)
