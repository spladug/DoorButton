The Big Red Button
==================

<img src="http://i.imgur.com/XxsloxI.jpg" alt="" align="right">

A set of terrible hacks to unlock a door when a button is pressed.

## Overview

There are two scripts, `redbutton.py` and `door-control.py`.

`redbutton.py` polls the USB interface to determine when the Big Red Button has
been pressed and sends DBus events accordingly.

`door-controller.py` listens to DBus and talks to the Brivo ACS OnSite admin
interface to remotely activate the door.

## Installation

```
cat <<END | sudo tee /etc/door-controller.ini
[door-control]
host = 192.168.1.123
username = redbutton
password = supersecret
END
sudo cp redbutton.py /usr/local/sbin/redbutton
sudo cp door-controller.py /usr/local/sbin/door-controller
sudo cp *.conf /etc/init/
```
