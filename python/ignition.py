#!/usr/bin/env - python

import serial
import struct
import time
import json
import argparse
import os
import emoji


# [
# [index, delay until next pin, [fire pin, fire pin2, fire pin 3, ...]],
# 
CONFIG_FILE = 'ignition.json'
RECOVERY_FILE = 'ignition_recovery.json'

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
    print "I'm going to run this show; starting at set %i with %i total sets:" % (start_set, len(firing_order))
    total_time = 0
    for idx, fire_command in enumerate(firing_order):
        if idx < start_set:
            print "Skipping set", idx
            continue
        print "Set:", idx 
        print "\tfire pins:", fire_command[1]
        print "\tthen delay:", fire_command[0], "seconds"
        total_time = total_time + fire_command[0]
    print "Total show time is", total_time, "seconds"



def write_recovery(last_set, pin):
    pass

def run_show(firing_order, start_set = 0):
    

    ser = setup_serial('/dev/tty.usbserial-DA01GYCL', 9600)

    for idx, fire_command in enumerate(firing_order):
        if idx < start_set:
            print "\nSkipping set", idx
            continue

        comm_status = comm_check(ser)
        print "\nRunning set", idx
        delay_in_seconds = fire_command[0]
        print '\tFiring pin(s)', fire_command[1],
        ret = fire(ser, fire_command[1])
        if ret != 0:
            with open(RECOVERY_FILE, 'wt') as rf:
                rf.write('[%i, %i]\n' % (idx, ret))
                rf.close()
            print "\n\nI didn't get an OK from the firing computer for set", idx, "pin", ret
            print "Recovery file '%s' written; run with -r to retry from set %i." % (RECOVERY_FILE, idx)
            exit()

        print '\tSleeping', delay_in_seconds, 'seconds'
        time.sleep(delay_in_seconds)

def comm_check(ser):
    print "Checking serial connectivity:",
    print emoji.emojize(":clock1:", use_aliases=True),
    ser.write(struct.pack("cb", "K", 0))
    status = ser.read()
    if status != 'A':
        print emoji.emojize(":x:", use_aliases=True),
        return 1 
    print emoji.emojize(":100:", use_aliases=True),
    print "\n"
    return 0

def fire(ser, pins):
    for pin in pins:
        print emoji.emojize(":fire:  :fireworks: "),
        ser.write(struct.pack("cb", "H", pin))
        status = ser.read()
        if status != 'A':
            return pin 
        print emoji.emojize(":sparkles:"),
    print "\n"
    return 0
            
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--comm", help="Check communication with the arduino and exit",
                        action="store_true")
    parser.add_argument("-t", "--test", help="Trigger each pin in order, sleeping for 3 seconds",
                        action="store_true")
    parser.add_argument("-r", "--recover", help="Recover from a failed run",
                        action="store_true")
    parser.add_argument("-f", "--fire", type=int, help="Fire a single pin")

    parser.add_argument("--gogogo", help="Actually run the show",
                        action="store_true")

    parser.add_argument("-d", "--dump", help="Dump the expected show and exit",
                        action="store_true")
    args = parser.parse_args()

    print args

    firing_order = load_firing_order()
    start_set = 0

    if args.dump:
        display_show(firing_order, start_set)
        exit()

    if args.fire:
        firing_order = []
        firing_order.append([0, [args.fire]])
    elif args.comm:
        ser = setup_serial('/dev/tty.usbserial-DA01GYCL', 9600)
        comm_check(ser)
        exit()
    elif args.test:
        firing_order = []
        for pin in range(26, 50):
            firing_order.append([0, [pin]])
    elif args.recover:
        with open(RECOVERY_FILE, 'rt') as rf:
            recovery_point = json.load(rf)
            rf.close()
            os.unlink(RECOVERY_FILE)
            print "Recovering to (zero-indexed) set:", recovery_point[0]
            start_set = recovery_point[0]

    if not args.gogogo:
        print "No --gogogo so running in dry run mode, will not trigger any pins."

    display_show(firing_order, start_set)

    if args.gogogo:
        run_show(firing_order, start_set=start_set)


if __name__ == '__main__':
    main()
