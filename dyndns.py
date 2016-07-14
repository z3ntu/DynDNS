#!/usr/bin/env python
import json
import os
import socket
import sys

import flask
import requests

import config_server

do_api_base = "https://api.digitalocean.com"
request_header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + config_server.do_token}
app = flask.Flask(__name__)

os.makedirs("letsencrypt-webroot/.well-known/acme-challenge", exist_ok=True)

@app.route('/')
def root():
    return "DynDNS server by z3ntu."


@app.route('/update_record', methods=['POST'])
def update_record():
    # Initialize variables
    action = ""
    ipv4 = False
    ipv6 = False

    if not flask.request.json:
        return "No body."
    if not flask.request.json.get('auth_key') or not flask.request.json.get('host') or not flask.request.json.get(
            'ip'):
        return "Missing parameter."
    try:
        socket.inet_pton(socket.AF_INET6, flask.request.json.get('ip'))
        ipv6 = True
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET, flask.request.json.get('ip'))
            ipv4 = True
        except OSError:
            return "Invalid IPv4/IPv6."
    if not is_valid_auth_key(flask.request.json.get('auth_key')):
        return "Invalid key."
    records_req = requests.get(do_api_base + "/v2/domains/" + config_server.do_domain + "/records",
                               headers=request_header)
    if records_req.status_code != 200:
        return "Internal error: " + str(records_req.status_code) + " - " + records_req.reason
    records = json.loads(records_req.text)
    record_id = None
    for record in records.get('domain_records'):
        if record.get('name') == flask.request.json.get('host'):
            if record.get("data") == flask.request.json.get('ip'):
                return "IP is the same."
            # Correct record (requested)
            if record.get('type') == 'AAAA':
                if ipv6:
                    action = "update_ipv6"
                elif ipv4:
                    action = "delete_ipv6"
            elif record.get('type') == 'A':
                if ipv6:
                    action = "delete_ipv4"
                elif ipv4:
                    action = "update_ipv4"
            else:  # Neither A nor AAAA
                continue
            record_id = record.get('id')
            break
    if not record_id:
        return "Host not found."  # Create host???

    if action is "update_ipv6" or action is "update_ipv4":
        # Update existing record
        data = {"data": flask.request.json.get('ip')}
        requests.put(do_api_base + "/v2/domains/" + config_server.do_domain + "/records/" + str(record_id),
                     json=data,
                     headers=request_header)
    elif action is "delete_ipv4" or action is "delete_ipv6":
        # Delete old record
        requests.delete(do_api_base + "/v2/domains/" + config_server.do_domain + "/records/" + str(record_id),
                        headers=request_header)
        if ipv4:
            type = "A"
        elif ipv6:
            type = "AAAA"
        else:
            return "Error."
        # Create new record
        data = {"type": type, "name": flask.request.json.get('host'), "data": flask.request.json.get('ip')}
        requests.post(do_api_base + "/v2/domains/" + config_server.do_domain + "/records",
                      json=data,
                      headers=request_header)
    return "Success."


@app.route('/.well-known/acme-challenge/<path:filename>')
def letsencrypt_handler(filename):
    return flask.send_from_directory("letsencrypt-webroot/.well-known/acme-challenge", filename)


def is_valid_auth_key(key):
    for line in [line.rstrip('\n') for line in open('auth_keys')]:
        if line == key:
            return True
    return False


if __name__ == '__main__':
    if config_server.use_wsgi:
        try:
            app.run()
        except OSError as err:
            print("[ERROR] " + err.strerror, file=sys.stderr)
            print("[ERROR] The program will now terminate.", file=sys.stderr)
    else:
        try:
            app.run(host=config_server.host,
                    port=config_server.port,
                    debug=config_server.debug)
        except OSError as err:
            print("[ERROR] " + err.strerror, file=sys.stderr)
            print("[ERROR] The program will now terminate.", file=sys.stderr)
