#!/usr/bin/python3

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
    MAX_UPLINK_LENGTH = 12 # in bytes

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

    def wait_for(self, success, failure, timeout):
        return self.receive_until(success, failure, timeout).decode() != ''

    def receive_until(self, success, failure, timeout):
        old_timeout = self.ser.timeout
        self.ser.timeout = timeout
        current_msg = self.ser.read_until(success.encode())
        self.ser.timeout = old_timeout
        if success in current_msg.decode():
            return current_msg
        elif failure in current_msg.decode():
            logging.warning('Failure ({})'.format(current_msg.decode().replace('\r\n', '')))
        else:
            logging.error('Receive timeout ({})'.format(current_msg.decode().replace('\r\n', '')))
        return ''

    def init_modem(self):
        if self.ser.is_open is True: # on some platforms the serial port needs to be closed first
            self.ser.close()

        try:
            self.ser.open()
        except serial.SerialException as e:
            logging.error("Could not open serial port {}: {}\n".format(self.ser.name, e))
            return

        self.ser.write('AT\r'.encode())
        if self.wait_for('OK', 'ERROR', 3):
            logging.info('SigFox Modem OK')
        else:
            logging.warning('SigFox Modem Init Error')
            self.ser.close()
            return

        self.ser.write('ATE0\r'.encode())
        if self.wait_for('OK', 'ERROR', 3):
            logging.info('SigFox Modem echo OFF')
        else:
            logging.warning('SigFox Modem Configuration Error')
            self.ser.close()
            return

        return self.ser


    def send_message(self, bytestring):

        self.init_modem()

        if self.ser.is_open:
            logging.info('Sending SigFox Message...')
            if len(bytestring) > self.MAX_UPLINK_LENGTH:
                logging.warning("Message longer than 12 bytes. Truncating ...")
            self.ser.write("AT$SF={0},2,0\r".format(bytestring[:self.MAX_UPLINK_LENGTH].hex()).encode())
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
    sgfx.send_message(message.encode(encoding="utf-8"))
