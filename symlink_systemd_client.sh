#!/bin/bash

this=$(pwd)
systemdloc=/etc/systemd/system/

sudo ln -s $this/dyndns.service $systemdloc
sudo ln -s $this/dyndns.timer $systemdloc
