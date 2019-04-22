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

import re
import logging

import serial

class Sigfox:
    MAX_UPLINK_LENGTH = 12 # in bytes
    DOWNLINK_START_TIMEOUT = 20
    DOWNLINK_RECEIVE_TIMEOUT = 25

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
        return bool(self.receive_until(success, failure, timeout).decode())

    def receive_until(self, success, failure, timeout):
        old_timeout = self.ser.timeout
        self.ser.timeout = timeout
        current_msg = self.ser.read_until(success.encode())
        logging.debug("Received: '{}' (decoded: '{}')".format(current_msg.hex(), current_msg.decode(errors='replace')))
        self.ser.timeout = old_timeout
        if success in current_msg.decode():
            return current_msg
        elif failure in current_msg.decode():
            logging.warning('Failure ({})'.format(current_msg.decode().replace('\r\n', '')))
        else:
            logging.error('Receive timeout ({})'.format(current_msg.decode().replace('\r\n', '')))
        return None

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
                logging.warning("Trying to send message longer than 12 bytes. Truncating ...")
                bytestring = bytestring[:self.MAX_UPLINK_LENGTH]
            self.ser.write("AT$SF={0},2,0\r".format(bytestring.hex()).encode())
            logging.info('Sending ...')
            if self.wait_for('OK', 'ERROR', 15):
                logging.info('OK Message sent')
                self.ser.close()
                return bytestring
            else:
                logging.error('Error sending message')
        else:
            logging.error('SigFox Modem Error')

        self.ser.close()
        return None

    def send_receive_message(self, bytestring):

        self.init_modem()

        if self.ser.is_open:
            logging.info('Sending SigFox Message...')
            if len(bytestring) > self.MAX_UPLINK_LENGTH:
                logging.warning("Message longer than 12 bytes. Truncating ...")
            self.ser.write("AT$SF={0},2,1\r".format(bytestring[:self.MAX_UPLINK_LENGTH].hex()).encode())
            logging.info('Sending ...')
            if self.wait_for('OK', 'ERROR', 15):
                logging.info('OK Message sent')
            else:
                logging.error('Error sending message')
                self.ser.close()
                return None

            if self.wait_for('BEGIN', 'ERROR', self.DOWNLINK_START_TIMEOUT + 2):
                logging.info('Waiting for answer')
            else:
                logging.error('Error waiting for answer')
                self.ser.close()
                return None

            rx_data = self.receive_until('END', 'ERROR', self.DOWNLINK_RECEIVE_TIMEOUT + 2)
            if rx_data:
                logging.info('Answer received')
                rx_data = rx_data.decode()
                logging.debug(rx_data)
                self.ser.close()
                match = re.match(r'\+RX=([0-9a-fA-F ]{2,})\+RX END', rx_data.replace('\r\n', ''))
                if match:
                    return bytes.fromhex(match.group(1))
                else:
                    logging.warning("Malformed or empty answer")
                    return None

            else:
                logging.warning('Error receiving answer')
                self.ser.close()
                return None

        else:
            logging.error('SigFox Modem Error')
            self.ser.close()
