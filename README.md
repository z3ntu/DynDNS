# DynDNS

DynDNS server & client in use with the DigitalOcean DNS.

## Requirements (Server)
* Python (+ flask, requests)
* Apache (+ mod_wsgi) (or any other WSGI capable software)

## Requirements (Client)
* Fish shell *(you can rewrite the client to any other shell, such as bash, but because I use fish everywhere and I like the syntax, I use it)*
* curl

## Setup (Server)
* Clone this repo into `/srv/dyndns`
* Copy `config_server.DEFAULT.py` to `config_server.py` and adjust the values.
* Copy `auth_keys.DEFAULT` to `auth_keys` and adjust the values (one key per line).
* Symlink the wsgi conf to `/etc/httpd/conf/extra/dyndns_wsgi.conf`
* Put the line `Include conf/extra/dyndns_wsgi.conf` into `/etc/httpd/conf/httpd.conf` (somewhere at the end).
* Get rid of the SSL stuff if you don't want SSL, otherwise get yourself a certificate.

## Setup (Client)
* Clone this repo somewhere.
* Copy `config.DEFAULT.sh` to `config.sh` and adjust the values.
* Either run `./client.sh` or follow the next steps.
* Symlink `dyndns.service` to `/etc/systemd/system/` and `dyndns.timer` to `/etc/systemd/system/`
* Symlink `/etc/systemd/system/dyndns.timer` to `/etc/systemd/system/timers.target.wants/` to enable the timer at boot.
* Hope for the best!
