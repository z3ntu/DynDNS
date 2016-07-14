#!/usr/bin/env python
import json
import socket
import sys

import config_server
import flask
import requests

do_api_base = "https://api.digitalocean.com"
request_header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + config_server.do_token}
app = flask.Flask(__name__)


@app.route('/update_record', methods=['POST'])
def update_record():
    if not flask.request.json:
        return "No body."
    if not flask.request.json.get('auth_key') or not flask.request.json.get('host') or not flask.request.json.get(
            'ip'):
        return "Missing parameter."
    try:
        socket.inet_pton(socket.AF_INET6, flask.request.json.get('ip'))
    except OSError:
        return "Invalid IPv6."
    if not is_valid_auth_key(flask.request.json.get('auth_key')):
        return "Invalid key."
    print("Change DO entry.")
    records_req = requests.get(do_api_base + "/v2/domains/" + config_server.do_domain + "/records",
                               headers=request_header)
    records = json.loads(records_req.text)
    record_id = None
    for record in records.get('domain_records'):
        print(record)
        if record.get('name') == flask.request.json.get('host') and record.get('type') == 'AAAA':
            if record.get("data") == flask.request.json.get('ip'):
                return "IP is the same."
            record_id = record.get('id')
            break
    if not record_id:
        return "Host not found."
    data = {"data": flask.request.json.get('ip')}
    print(flask.request.json.get("ip"))
    requests.put(do_api_base + "/v2/domains/" + config_server.do_domain + "/records/" + str(record_id),
                 json=data,
                 headers=request_header)
    return "Success."


def is_valid_auth_key(key):
    print(key)
    return True


if __name__ == '__main__':
    try:
        app.run(host=config_server.host,
                port=config_server.port,
                debug=config_server.debug)
    except OSError as err:
        print("[ERROR] " + err.strerror, file=sys.stderr)
        print("[ERROR] The program will now terminate.", file=sys.stderr)
