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

    # Check if there's a request body
    if not flask.request.json:
        return "No body."
    # Check if all parameters are given
    if not flask.request.json.get('auth_key') or not flask.request.json.get('host') or not flask.request.json.get(
            'ip'):
        return "Missing parameter."
    # Check if the given IP is IPv4 or IPv6
    try:
        socket.inet_pton(socket.AF_INET6, flask.request.json.get('ip'))
        ipv6 = True
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET, flask.request.json.get('ip'))
            ipv4 = True
        except OSError:
            return "Invalid IPv4/IPv6."
    try:
        if not is_valid_auth_key(flask.request.json.get('auth_key')):
            return "Invalid key."
    except FileNotFoundError:
        return "'auth_keys' file not found. Please fix your server."
    # set the initial request url
    do_request_url = do_api_base + "/v2/domains/" + config_server.do_domain + "/records"
    records = {}
    # loop for multiple pages
    while True:
        records_req = requests.get(do_request_url,
                                   headers=request_header)
        if records_req.status_code != 200:
            return "Internal error: " + str(records_req.status_code) + " - " + records_req.reason
        # 'internal' records variable
        records_int = json.loads(records_req.text)
        if not records_int.get('links'):  # if there are multiple pages
            # Just set the variable without extending it
            records = records_int
            break
        # get the request url for the next page
        do_request_url = records_int.get('links').get('pages').get('next')
        # if 'records' is empty, set it, otherwise extend the 'domain_records' variable
        if not records:
            records = records_int
        else:
            records.get('domain_records').extend(records_int.get('domain_records'))
        # if there's no 'next' url, we are at the last page -> break out of the loop
        if not do_request_url:
            break
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
        return "Host not found."  # Should we create the host here?
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


# Handle LetsEncrypt/Certbot requests
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
