#!/usr/bin/env python3

import serial
import struct
import time
import json
import argparse
import os
import emoji

from threading import Thread


# [
# [index, delay until next pin, [fire pin, fire pin2, fire pin 3, ...]],
# 
CONFIG_FILE = 'configs/ignition.json'
RECOVERY_FILE = 'configs/ignition_recovery.json'

class FiringException(Exception):
    def __init__(self, firing_state, current_set):
        self.firing_state = firing_state
        self.current_set = current_set

    def __str__(self):
        return (repr(self.current_set), repr(self.firing_state))

def load_firing_order():
  with open(CONFIG_FILE, 'rt') as f:
	  return json.load(f)

def setup_serial(ser_port, rate):
	return serial.Serial(ser_port, rate, timeout=1)


def display_show(firing_order, start_set):
    print("I'm going to run this show; starting at set {} with {} total sets:".format(start_set, len(firing_order)))
    total_time = 0
    for idx, fire_command in enumerate(firing_order):
        if idx < start_set:
            print("Skipping set {}".format(idx))
            continue
        print("Set: {}".format(idx))
        print("\tfire pins: {}".format(fire_command[1]))
        print("\tthen delay: {} seconds".format(fire_command[0]))
        total_time = total_time + fire_command[0]
    print("Total show time is {} seconds.".format(total_time))


def input_thread(keyboard_buffer):
    input()
    keyboard_buffer.append(None)


def write_recovery(last_set, pin):
    pass

def run_show(firing_order, start_set = 0, dry_run=True):


    if not dry_run:
        ser = setup_serial('/dev/tty.usbserial-DA01L2G9', 9600)
    else:
        ser = None

    for idx, fire_command in enumerate(firing_order):
        if idx < start_set:
            print("\nSkipping set {}".format(idx))
            continue

        comm_status = comm_check(ser, dry_run)
        print("\nRunning set {}".format(idx))
        delay_in_seconds = fire_command[0]
        print('\tFiring pin(s) {}'.format(fire_command[1]), end="")
        ret = fire(ser, fire_command[1], dry_run)

        if ret != 0:
            with open(RECOVERY_FILE, 'wt') as rf:
                rf.write('[%i, %i]\n' % (idx, ret))
                rf.close()
            print("\n\nI didn't get an OK from the firing computer for set {} pin {}".format(idx, ret))
            print("Recovery file '{}' written; run with -r to retry from set {}.".format(RECOVERY_FILE, idx))
            exit()

        print('\tSleeping {} seconds; press "s" to skip.'.format(delay_in_seconds))

#        time.sleep(delay_in_seconds)
        keyboard_buffer = []
        t = Thread(target=input_thread, args=(keyboard_buffer,))
        t.start()
        while delay_in_seconds > 0:
            time.sleep(1)
            delay_in_seconds = delay_in_seconds - 1
            print("\t{} seconds remaining\r".format(delay_in_seconds), end='\r')
            if keyboard_buffer: break

def comm_check(ser, dry_run=True):
    print("Checking serial connectivity:")
    print(emoji.emojize(" :clock1: ", use_aliases=True), end="")
    if not dry_run:
        ser.write(struct.pack("cb", b'K', 0))
        status = ser.read()
        if status != b'A':
            print(emoji.emojize(" :x: ", use_aliases=True))
            return 1
    else:
        print("XXX DRY RUN XXX", end="")
    print(emoji.emojize(" :100: ", use_aliases=True), end="")
    print("\n")
    return 0

def fire(ser, pins, dry_run=True):
    for pin in pins:
        print (emoji.emojize(" :fire:  :fireworks: "), end="")
        if not dry_run:
            ser.write(struct.pack("cb", b'H', pin))
            status = ser.read()
            if status != b'A':
                return pin
        else:
            print("XXX DRY RUN XXX", end="")
        print(emoji.emojize(" :sparkles: "), end="")
    print("\n")
    return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--comm", help="Check communication with the arduino and exit",
                        action="store_true")
    parser.add_argument("-a", "--all_pins", help="Trigger each pin in order, sleeping for 3 seconds",
                        action="store_true")
    parser.add_argument("-r", "--recover", help="Recover from a failed run",
                        action="store_true")
    parser.add_argument("-f", "--fire", type=int, help="Fire a single pin")

    parser.add_argument("--gogogo", help="Actually run the show",
                        action="store_true")

    parser.add_argument("-d", "--dump", help="Dump the expected show and exit",
                        action="store_true")
    args = parser.parse_args()

    print(args)

    firing_order = load_firing_order()
    start_set = 0

    if args.dump:
        display_show(firing_order, start_set)
        exit()

    if args.fire:
        firing_order = []
        firing_order.append([0, [args.fire]])
    elif args.comm:
        ser = setup_serial('/dev/tty.usbserial-DA01L2G9', 9600)
        comm_check(ser, False)
        exit()
    elif args.all_pins:
        firing_order = []
        for pin in range(26, 50):
            firing_order.append([0, [pin]])
    elif args.recover:
        with open(RECOVERY_FILE, 'rt') as rf:
            recovery_point = json.load(rf)
            rf.close()
            os.unlink(RECOVERY_FILE)
            print("Recovering to (zero-indexed) set: {}".format(recovery_point[0]))
            start_set = recovery_point[0]

    dry_run = True
    if not args.gogogo:
        print("No --gogogo so running in dry run mode, will not trigger any pins.")

    display_show(firing_order, start_set)

    if args.gogogo:
        dry_run = False

    run_show(firing_order, start_set=start_set, dry_run=dry_run)


if __name__ == '__main__':
    main()
