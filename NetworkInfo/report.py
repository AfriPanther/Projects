import sys
import subprocess
import time
import requests
import json
import texttable


class report:
    def __init__(self, json_file, out_file):
        self.json = json_file
        pass



def main():
    if len(sys.argv) < 1 or len(sys.argv) > 4:
        sys.stderr.write('Incorrect number of arguments.\n')
        sys.exit(-1)

    json_in = sys.argv[1]
    output = sys.argv[2]
    text = ""

    with open(json_in) as f:
        json_data = json.load(f)
 

    # Table 1: Al information gathered by scan.py
    table = texttable.Texttable(0)
    table.set_cols_align(["c"] * 13)
    table.set_cols_valign(["m"] * 13)
    my_headers = ["Domain", "geo_locations", "hsts",
                  "http_server", "insecure_http", "ipv4_addresses", 
                  "ipv6_addresses", "rdns_names", "redirect_to_https", 
                  "root_ca", "rtt_range", "scan_time", "tls_versions"]

    readout = [my_headers]
    for domain in json_data:
        domain_row = [domain]
        for element in json_data[domain]:
            if isinstance(element, list):
                domain_row.extend(json_data[domain][element])
            elif json_data[domain][element] is None:
                domain_row.extend(["None"])
            elif json_data[domain][element] == 1:
                domain_row.extend(["True"])
            elif json_data[domain][element] == 0:
                domain_row.extend(["False"])      
            else:
                domain_row.extend([json_data[domain][element]])
        readout.extend([domain_row])

    table.add_rows(readout)
    text += table.draw() + "\n\n\n" 


    # TABLE 2: A table showing the RTT ranges for all domains, 
    #          sorted by the minimum RTT (ordered from fastest to slowest).
    table = texttable.Texttable(0)
    table.set_cols_align(["c"] * 2)
    table.set_cols_valign(["m"] * 2)
    my_headers = ["Domain", "rtt_range"]
    readout = [my_headers]
    rtt_dict = {}
    na = {}
    for domain in json_data:
        if None in json_data[domain]['rtt_range']:
            na[domain] = json_data[domain]['rtt_range']
        else:
            rtt_dict[domain] = json_data[domain]['rtt_range']
    sorted_data = dict(sorted(rtt_dict.items(), key=lambda item: item[1]))
    sorted_data.update(na)

    for domain in sorted_data:
        domain_row = [domain, sorted_data[domain]]
        readout.extend([domain_row])

    table.add_rows(readout)
    text += table.draw() + "\n\n\n" 


    # TABLE 3: A table showing the number of occurrences for each 
    #          observed root certificate authority (from Part 2i), sorted
    #          from most popular to least.
    table = texttable.Texttable(0)
    table.set_cols_align(["c"] * 2)
    table.set_cols_valign(["m"] * 2)
    my_headers = ["Root CA", "Occurrences"]
    readout = [my_headers]
    authority = {}

    for domain in json_data:
        if json_data[domain]['root_ca'] in authority:
            authority[json_data[domain]['root_ca']] += 1
        else:
            authority[json_data[domain]['root_ca']] = 1

    sorted_roots = dict(sorted(authority.items(), key=lambda item: item[1], reverse = True))

    for domain in sorted_roots:
        domain_row = [domain, sorted_roots[domain]]
        readout.extend([domain_row])

    table.add_rows(readout)
    text += table.draw() + "\n\n\n" 



    # TABLE 4: A table showing the number of occurrences of each web server (from Part 2d), 
    #          ordered from most popular to least.
    table = texttable.Texttable(0)
    table.set_cols_align(["c"] * 2)
    table.set_cols_valign(["m"] * 2)
    my_headers = ["Web Server", "Occurrences"]
    readout = [my_headers]
    servers = {}

    for domain in json_data:
        if json_data[domain]['http_server'] in servers:
            servers[json_data[domain]['http_server']] += 1
        else:
            servers[json_data[domain]['http_server']] = 1

    sorted_servers = dict(sorted(servers.items(), key=lambda item: item[1], reverse = True))

    for server in sorted_servers:
        server_row = [server, sorted_servers[server]]
        readout.extend([server_row])

    table.add_rows(readout)
    text += table.draw() + "\n\n\n" 


    # TABLE 5: A table showing the percentage of scanned domains supporting:
    #          - each version of TLS listed in Part 2h. I expect to see close
    #               to zero percent for SSLv2 and SSLv3. "tls_versions"
    #          - "plain http" (Part 2e) "insecure_http"
    #          - "https redirect" (Part 2f) "redirect_to_https"
    #          - "hsts" (Part 2g) "hsts"
    #          - "ipv6" (from Part 2c) "ipv6_addresses"
    table = texttable.Texttable(0)
    table.set_cols_align(["c"] * 2)
    table.set_cols_valign(["m"] * 2)
    my_headers = ["Systems", "Percent Supported"]
    readout = [my_headers]
    type_count = {"plain http": 0, 
                  "https redirect": 0, 
                  "hsts": 0, 
                  "ipv6": 0, 
                  "SSLv2": 0, 
                  "SSLv3": 0, 
                  "TLSv1.0": 0, 
                  "TLSv1.1": 0, 
                  "TLSv1.2": 0}

    for domain in json_data:
        if json_data[domain]['insecure_http']:
            type_count['plain http'] += 1
        if json_data[domain]['redirect_to_https']:
            type_count['https redirect'] += 1
        if json_data[domain]['hsts']:
            type_count['hsts'] += 1
        if json_data[domain]['ipv6_addresses'] is not None:
            type_count['ipv6'] += 1
        if 'SSLv2' in json_data[domain]['tls_versions']:
            type_count['SSLv2'] += 1
        if 'SSLv3' in json_data[domain]['tls_versions']:
            type_count['SSLv3'] += 1
        if 'TLSv1.0' in json_data[domain]['tls_versions']:
            type_count['TLSv1.0'] += 1
        if 'TLSv1.1' in json_data[domain]['tls_versions']:
            type_count['TLSv1.1'] += 1
        if 'TLSv1.2' in json_data[domain]['tls_versions']:
            type_count['TLSv1.2'] += 1

    for item in type_count:
        percent = (type_count[item] / len(json_data)) * 100
        percent = format(percent, ">-05.2f")
        percent = str(percent) + '%'
        readout.extend([[item, percent]])

    table.add_rows(readout)
    text += table.draw() + "\n\n\n" 


    # Write to provided text file
    file1 = open(output, "w")
    file1.write(text)
    file1.close()

if __name__ == "__main__":
    main()

