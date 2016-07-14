#!/usr/bin/fish

source config.sh

set ip (curl -sS icanhazip.com)

echo "*** DynDNS Client - made by z3ntu ***"
echo "Your IP: $ip"
echo "Remote: $remote"
echo "Host: $host"
echo 
set data "{\"auth_key\": \"$auth_key\", \"host\": \"$host\", \"ip\": \"$ip\"}"
echo -n "Response: "
curl -sS -X POST -d "$data" $remote --header "Content-Type:application/json"
