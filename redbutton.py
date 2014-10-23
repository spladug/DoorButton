#!/usr/bin/python

import logging
import time
import subprocess

import usb


VENDOR_ID = 0x1d34
PRODUCT_ID = 0x000d
POLL_INTERVAL = 0.05  # seconds
OBJECT_PATH = "/com/dreamcheeky/BigRedButton"
INTERFACE_ROOT = "com.dreamcheeky.BigRedButton"


def send_signal(component, event):
    subprocess.check_call([
        "/usr/bin/dbus-send",
        "--system",
        OBJECT_PATH,
        "%s.%s%s" % (INTERFACE_ROOT, component, event),
    ])


def find_device(vendor_id, product_id):
    for bus in usb.busses():
        for device in bus.devices:
            if device.idVendor == vendor_id and device.idProduct == product_id:
                return device


def wait_for_events():
    device = find_device(VENDOR_ID, PRODUCT_ID)
    if not device:
        logging.error("could not find device")
        return

    handle = device.open()
    interface = device.configurations[0].interfaces[0][0]
    endpoint = interface.endpoints[0]

    try:
        handle.detachKernelDriver(interface)
    except usb.USBError:
        pass

    handle.claimInterface(interface)

    try:
        currently_pressed = False
        currently_lid_open = False

        while True:
            result = handle.controlMsg(
                requestType=0x21,  # OUT | CLASS | INTERFACE
                request=0x09,
                value=0x0200,
                buffer="\x00\x00\x00\x00\x00\x00\x00\x02",
            )

            try:
                result = handle.interruptRead(
                    endpoint.address, endpoint.maxPacketSize)
            except usb.USBError:
                pass
            else:
                pressed = not bool(result[0] & 0x01)
                if pressed != currently_pressed:
                    if pressed:
                        send_signal("Button", "Pressed")
                    else:
                        send_signal("Button", "Released")

                    currently_pressed = pressed

                lid_open = bool(result[0] & 0x02)
                if lid_open != currently_lid_open:
                    if lid_open:
                        send_signal("Lid", "Opened")
                    else:
                        send_signal("Lid", "Closed")

                    currently_lid_open = lid_open

            time.sleep(POLL_INTERVAL)
    finally:
        handle.releaseInterface()


if __name__ == "__main__":
    wait_for_events()
