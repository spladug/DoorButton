#!/usr/bin/python

import ConfigParser
import logging
import random
import threading
import time
import urlparse

import dbus
import gobject
import requests

from dbus.mainloop.glib import DBusGMainLoop


IDLE_TIME = 60.0  # seconds between auth re-ups


class Door(threading.Thread):
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.trigger = threading.Event()

        super(Door, self).__init__()
        self.daemon = True

    def open(self):
        self.trigger.set()

    def run(self):
        endpoint = urlparse.urlunparse((
            "https",
            self.host,
            "/cgi-bin/acs.fcgi",
            None,
            None,
            None,
        ))

        session = requests.Session()
        session.verify = False  # TODO

        # authenticate
        logging.info("authenticating")
        session.post(endpoint, data={
            "username": self.username,
            "password": self.password,
        })
        assert session.cookies["sess"]
        logging.info("authenticated")

        while True:
            logging.debug("waiting for trigger")
            open_door = self.trigger.wait(IDLE_TIME)

            try:
                if open_door:
                    logging.debug("pulsing door")
                    session.get(endpoint, params={
                        "cur": "devices",
                        "do": "pulse",
                        "id": "2",
                        "mode": "popup",
                        "opt": "pulse_output",
                    })
                else:
                    logging.debug("refreshing session")
                    session.get(endpoint, params={
                        "cur": "activity",
                        "opt": "feed_live_activity",
                        "mode": "popup",
                        "ajax": 1,
                        "page_length": 25,
                        "time": int(time.time()),
                        "rnd": random.randint(1, 100000),
                    })
                logging.debug("done")
            except requests.exceptions.RequestException as e:
                logging.exception(e)

            self.trigger.clear()


def main():
    parser = ConfigParser.RawConfigParser()
    with open("/etc/door-controller.ini", "r") as f:
        parser.readfp(f)

    logging.basicConfig(level=logging.DEBUG)

    door = Door(
        host=parser.get("door-control", "host"),
        username=parser.get("door-control", "username"),
        password=parser.get("door-control", "password"),
    )
    door.start()

    DBusGMainLoop(set_as_default=True)
    system_bus = dbus.SystemBus()
    system_bus.add_signal_receiver(
        door.open,
        dbus_interface="com.dreamcheeky.BigRedButton",
        signal_name="ButtonPressed",
    )

    gobject.threads_init()
    loop = gobject.MainLoop()
    loop.run()


if __name__ == "__main__":
    main()
