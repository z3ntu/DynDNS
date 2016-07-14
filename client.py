#!/usr/bin/env python

import requests
import subprocess
import config_client


def main():
    ipaddr = subprocess.check_output("ip -6 addr show " + config_client.interface + " scope global | grep 'inet6' | head -n1 | awk '{print $2}' | awk -F/ '{print $1}' | tr -d '\n'", shell=True).decode("utf-8")
    print(ipaddr)
    data = {"auth_key": config_client.auth_key, "host": config_client.host, "ip": ipaddr}
    response = requests.post(config_client.dyndns_url + ":" + str(config_client.dyndns_port) + "/update_record", json=data).text
    print(response)

if __name__ == '__main__':
    main()
