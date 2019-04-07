#!/usr/bin/python

## @package rpisigfox
#  This script allow the control of the rpisigfox expansion board for Raspberry Pi.
#
#  V1.0 allow only to send regular message on the SigFox Network.
#  syntax is :
#  sendsigfox MESSAGE
#  where MESSAGE is a HEXA string encoded. Can be 2 to 24 characters representing 1 to 12 bytes.
#  Example : sendsigfox 00AA55BF to send the 4 bytes 0x00 0xAA 0x55 0xBF
# 

import logging
import sys
from time import sleep

import serial

class Sigfox:
    SOH = chr(0x01)
    STX = chr(0x02)
    EOT = chr(0x04)
    ACK = chr(0x06)
    NAK = chr(0x15)
    CAN = chr(0x18)
    CRC = chr(0x43)

    def __init__(self, port="/dev/ttyAMA0", timeout=None):
        logging.debug('Serial port : {}'.format(port))
        self.ser = serial.Serial(
            port=port,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=timeout
        )

    def getc(self, size, timeout=1):
        return self.ser.read(size)

    def putc(self, data, timeout=1):
        self.ser.write(data)
        sleep(0.001) # give device time to prepare new buffer and start sending it

    def wait_for(self, success, failure, timeout):
        return self.receive_until(success, failure, timeout) != ''

    def receive_until(self, success, failure, timeout):
        iter_count = timeout / 0.1
        self.ser.timeout = 0.1
        current_msg = ''
        while iter_count >= 0 and success not in current_msg and failure not in current_msg:
            sleep(0.1)
            while self.ser.inWaiting() > 0: # bunch of data ready for reading
                c = self.ser.read()
                current_msg += c
            iter_count -= 1
        if success in current_msg:
            return current_msg
        elif failure in current_msg:
            logging.warning('Failure ({})'.format(current_msg.replace('\r\n', '')))
        else:
            logging.error('Receive timeout ({})'.format(current_msg.replace('\r\n', '')))
        return ''

    def send_message(self, message):
        print('Sending SigFox Message...')

        if self.ser.isOpen() is True: # on some platforms the serial port needs to be closed first
            self.ser.close()

        try:
            self.ser.open()
        except serial.SerialException as e:
            logging.error("Could not open serial port {}: {}\n".format(self.ser.name, e))
            sys.exit(1)

        self.ser.write('AT\r')
        if self.wait_for('OK', 'ERROR', 3):
            logging.info('SigFox Modem OK')

            self.ser.write("AT$SS={0}\r".format(message))
            logging.info('Sending ...')
            if self.wait_for('OK', 'ERROR', 15):
                logging.info('OK Message sent')

        else:
            logging.error('SigFox Modem Error')

        self.ser.close()

if __name__ == '__main__':

    if len(sys.argv) == 3:
        portName = sys.argv[2]
        sgfx = Sigfox(portName)
    else:
        sgfx = Sigfox()

    DEFAULT_MESSAGE = "1234CAFE"
    if len(sys.argv) > 1:
        message = "{0}".format(sys.argv[1])
    else:
        message = DEFAULT_MESSAGE
    sgfx.send_message(message)
