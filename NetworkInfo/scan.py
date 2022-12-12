import sys
import subprocess
import time
import requests
import json
import socket
import maxminddb


class scan:
	def __init__(self, txt_file, out_file):
		self.txt = txt_file
		pass


# Scan_time. Seconds since 1970
def scan_time(website):
	Timestamp = time.time()
	return Timestamp

# ip_addresses
def ip_addresses(website):
	IPv4 = []
	IPv6 = []
	# replace google.com with input
	result = subprocess.check_output(["nslookup", website, "8.8.8.8"], timeout=2, stderr=subprocess.STDOUT).decode("utf-8")
	# Start of the IPv4 Addresses
	parse = result.split()
	IP_index = parse.index('Address:', 3) + 1
	if '.' in parse[IP_index]:
		IPv4.append(parse[IP_index])
	elif ':' in parse[IP_index]:
		IPv6.append(parse[IP_index])

	# Two scenarios:
	# no IPv6's, so goes to the end
	# IPv6's, so need to stop at some point
	
	while 'Address:' in parse[IP_index:]:
		# Redefine IP index
		IP_index = parse.index('Address:', IP_index) + 1

		# Identify if IP is IPv4 or IPv6
		if '.' in parse[IP_index]:
			IPv4.append(parse[IP_index])
		elif ':' in parse[IP_index]:
			IPv6.append(parse[IP_index])
		else:
			pass

	if len(IPv4) < 1:
		IPv4 = None
	if len(IPv6) < 1:
		IPv6 = None

	return IPv4, IPv6

	# http_server
	# Probably want to learn to use python's Requests library. 
	# We want the server software reported in the server header of the HTTP response.
	# output can be null

def http_server(website):
	try:
		result = requests.get('http://' + website, timeout=10)
		pass
	except Exception as e:
		return None
	else:
		pass

	try:
		header = result.headers['server']
		pass
	except Exception as e:
		
		return None
		raise e
	else:
		return header
		pass

	# insecure_http
	# Return a boolean if the website listens for unencrypted HTTP requests at port 80
	# send a request, and if it doesn't fail, return True?

def insecure_http(website):
	# Might need to edit website if port line already exists
	url_80 = str('http://' + website + ':80')
	try:
		result = requests.get(url_80, timeout=10)
		pass
	except Exception as e:
		return False
	else:
		pass
	# Check to see if successful
	if result.ok:
		return True
	else:
		return False
	
	# redirect_to_https

	# return bool if unencrypted requests to port 80 are redirected
	# If the STATUS CODE starts with '30' then it is a redirect.
	# Check the location header to see if it redirects to https
def redirect_to_https(website):
	url_80 = str('http://' + website + ':80')
	try:
		session = requests.Session()
		session.max_redirects = 10
		# session.get(url)
		result = session.get(url_80, timeout=10)
		pass
	except Exception as e:
		return None
	else:
		pass
	if result.url[0:5] == 'https':
			return True
	return False

def hsts(website):
	url = 'http://' + website
	try:
		result = requests.get(url, timeout=5)
		pass
	except Exception as e:
		return None
	else:
		pass
	# check for header! if it exists, return true.
	try:
		header = result.headers['Strict-Transport-Security']
		pass
	except Exception as e:
		return False
	else:
		return True
		pass

# Grabs the compatible TLS versions of the domain/website.
def tls_versions(website):
	TLS_list = []
	# Check for SSLv2, SSLv3, TLSv1.0, TLSv1.1, and TLSv1.2 compatibility
	try:
		result = subprocess.check_output(["nmap", '--script', 'ssl-enum-ciphers', '-p', '443', website], timeout=10, stderr=subprocess.STDOUT).decode("utf-8")
	except Exception as e:
		pass
	else:
		if 'SSLv2' in result:
			TLS_list.append('SSLv2')
		if 'SSLv3' in result:
			TLS_list.append('SSLv3')
		if 'TLSv1.0' in result:
			TLS_list.append('TLSv1.0')
		if 'TLSv1.1' in result:
			TLS_list.append('TLSv1.1')
		if 'TLSv1.2' in result:
			TLS_list.append('TLSv1.2')
		pass

	# Check for TLSv1.3. If it fails, does not support TLSv1.3
	try:
		result = subprocess.check_output(["openssl", "s_client", '-tls1_3', '-connect', (website + ':443')], input=b'', timeout=10, stderr=subprocess.STDOUT).decode("utf-8")
	except Exception as e:
		pass
	else:
		TLS_list.append('TLSv1.3')
	return TLS_list

def root_ca(website):
	try:
		result = subprocess.check_output(["openssl", "s_client", '-connect', (website + ':443')], input=b'', timeout=10, stderr=subprocess.STDOUT).decode("utf-8")
	except Exception as e:
		return None
		pass
	else:
		pass

	# Find the root certificate!
	start = result.find('O = ') + 4
	end = result.find(',', start)
	if start == -1:
		return None
	if result[start] == '"':
		return result[start+1:end]

	return str(result[start:end])

# reverse dns lookup addresses!
def rdns_names(ips):
	names = []
	for ip in ips:
		try:
			# Tries to get host names from IP address. May fail
			aliases = socket.gethostbyaddr(ip)
		except Exception as e:
			pass
		else:
			# Returned successfully! Therefore...
			# ...check first index for local host name.
			# if host is already catalogued, ignore. Append if new
			if aliases[0] not in names:
				names.append(aliases[0])
			# Look through list of aliases and do the same as bove.
			for alias in aliases[1]:
				if alias not in names:
					names.append(alias)
	return names

def rtt_range(ips):
	port = 80
	times = []

	for host in ips:
		url = 'http://' + host + ':80'
		host_port = (host, port)
		try:
			A = time.time()
			result = requests.get(url, timeout=6)
		except Exception as e:
			try:
				url = 'http://' + host + ':22'
				A = time.time()
				result = requests.get(url, timeout=6)
			except Exception as e:
				try:
					url = 'http://' + host + ':443'
					A = time.time()
					result = requests.get(url, timeout=6)
				except Exception as e:
					times.append(None)
					continue
					pass
				else:
					pass
				pass
			else:
				pass
			pass
		else:
			pass
		B = time.time()
		# calculate RTT and add it to list
		RTT = (B - A)*1000
		times.append(RTT)

		# Second time
		for host in ips:
			url = 'http://' + host + ':80'
			host_port = (host, port)
			try:
				A = time.time()
				result = requests.get(url, timeout=6)
			except Exception as e:
				try:
					url = 'http://' + host + ':22'
					A = time.time()
					result = requests.get(url, timeout=6)
				except Exception as e:
					try:
						url = 'http://' + host + ':443'
						A = time.time()
						result = requests.get(url, timeout=6)
					except Exception as e:
						times.append(None)
						continue
						pass
					else:
						pass
					pass
				else:
					pass
				pass
			else:
				pass
			B = time.time()
			# calculate RTT and add it to list
			RTT = (B - A)*1000
			times.append(RTT)
	# if domain is unreachable, return null value
	try:
		min_max = [min(times), max(times)]
	except Exception as e:
		return [None, None]
		pass
	else:
		return [min(times), max(times)]

def geo_locations(ips):
	locations = []
	city = ''
	province = ''
	country = ''
	
	reader = maxminddb.open_database('GeoLite2-City.mmdb')
	# For every ip address, look for the corresponding city, province, and country.
	for host in ips:
		geography = reader.get(host)
		try:
			city = geography['city']['names']['en'] + ', '
		except Exception as e:
			city = ''
			pass
		else:
			pass

		# Check for province 
		try:
			province = geography['subdivisions'][0]['names']['en'] + ', '
		except Exception as e:
			province = ''
			pass
		else:
			pass

		#Check for country
		try:
			country = geography['country']['names']['en']
		except Exception as e:
			country = ''
			pass
		else:
			pass
		locations.append(city + province + country)
	
	locations = list(set(locations))
	return locations

def main():
	if len(sys.argv) < 1 or len(sys.argv) > 3:
		sys.stderr.write('Incorrect number of arguments.\n')
		sys.exit(-1)
	# Thinking that there are more edge cases, but come back to that.
	txt = sys.argv[1]
	output = sys.argv[2]

	# Interpret the file!
	text_file = open(txt, 'r')
	Lines = text_file.readlines()	
	# populate elements
	elements = [e[:len(e) - 1] for e in Lines]
	if "\n" not in Lines[len(Lines) - 1]:
		elements[len(Lines)- 1] = Lines[len(Lines) - 1]
	
	out_dict = {}
	for name in elements:
		out_dict[name] = {}

	for website in elements:
		# a) Scan_time
		scantime = scan_time(website)
		out_dict[website]["scan_time"] = scantime
		
		# b-c) Get the IP addresses.
		IPv4_addr, IPv6_addr = ip_addresses(website)
		out_dict[website]["ipv4_addresses"] = IPv4_addr
		out_dict[website]["ipv6_addresses"] = IPv6_addr

		# d) Server Software! # txt represents a single
		software_data = http_server(website)
		out_dict[website]["http_server"] = software_data

		# e) Insecure http? bool
		# TODO: Come back and make sure insecure bool is right
		# TODO: Make a limit on redirects
		insecure_bool = insecure_http(website)
		out_dict[website]["insecure_http"] = insecure_bool

		# f) Redirect_to_https?
		# TODO: Set max redirect
		redirect_https = redirect_to_https(website)
		out_dict[website]["redirect_to_https"] = redirect_https

		# g) hsts? bool
		# looks to see if HTTP Strict Transport Security header exists
		hsts_bool = hsts(website)
		out_dict[website]["hsts"] = hsts_bool

		# h) tls_versions
		# list all versions of Transport Layer security
		tls_types = tls_versions(website)
		out_dict[website]["tls_versions"] = tls_types

		# i) root_ca
		# list the root certificate authority (CA)
		root = root_ca(website)
		out_dict[website]["root_ca"] = root

		# j) rdns_names
		# List the revrse dns names for IPv4 addresses in b
		rdns_hosts = rdns_names(out_dict[website]["ipv4_addresses"])
		out_dict[website]["rdns_names"] = rdns_hosts

		# k) rtt_range
		rtt = rtt_range(out_dict[website]["ipv4_addresses"])
		out_dict[website]["rtt_range"] = rtt

		# L) geo_locations
		location_header = geo_locations(out_dict[website]["ipv4_addresses"])
		out_dict[website]["geo_locations"] = location_header

	with open(output, "w") as f:
		json.dump(out_dict, f, sort_keys=True, indent=4)

if __name__ == "__main__":
   main()

