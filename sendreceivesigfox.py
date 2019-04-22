#!/usr/bin/python3

## @package rpisigfox
#  This script allow the control of the rpisigfox expansion board for Raspberry Pi.
#
#  V1.0 allow only to send regular message on the SigFox Network.
#  syntax is :
#  sendsigfox MESSAGE
#  where MESSAGE is an HEXA string encoded. Can be 2 to 24 characters representing 1 to 12 bytes.
#  Example : sendsigfox 00AA55BF to send the 4 bytes 0x00 0xAA 0x55 0xBF
# 

import logging
import sys

from sigfox import Sigfox

if __name__ == '__main__':
    DEFAULT_PORT = '/dev/ttyAMA0'
    DEFAULT_MESSAGE = "1234CAFE"

    print('Sending SigFox Message...')
    # allow serial port choice from parameter - default is /dev/ttyAMA0
    try:
        port_name = sys.argv[2]
        print('Serial port : ' + port_name)
    except IndexError:
        port_name = DEFAULT_PORT
    sgfx = Sigfox(port_name)

    try:
        message = bytes.fromhex(sys.argv[1])
    except IndexError:
        message = bytes.fromhex(DEFAULT_MESSAGE)
    logging.getLogger().setLevel(logging.INFO)
    response = sgfx.send_receive_message(message)

    if response:
        print(response)
    else:
        print("No response")
