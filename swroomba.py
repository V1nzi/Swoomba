# the following is not how to code properly lol
# this is just extremely quick and dirty botching, so I can laugh at a roomba screaming in pain

import serial
import time
from enum import IntFlag
from random import random, randint
import glob
import pygame

WORK_DIR = '/home/pi/swroomba'
AUDIO_DIR = '/home/pi/swroomba/audio'

# command op codes
OP_START = 128
OP_SAFE = 131
OP_QUERY_LIST = 149
OP_DRIVE = 137

# sensor packet ids
PACKET_MODE = 35
PACKET_BUMPS = 7

# modes
MODE_SAFE = 2

class Bump(IntFlag):
    Nope = 0,
    Left = 1,
    Right = 2,
    Both = 3

class Turn(IntFlag):
    Clockwise = -1, # right
    CounterClockwise = 1 # left

def rand(min, max):
    return min + (random() * (max - min))

def wait(secs = 0.015):
    time.sleep(secs)

def get_bytes(number, length, signed=True):
    return number.to_bytes(length, byteorder='big', signed=signed)

def get_int(bytes):
    return int.from_bytes(bytes, byteorder='big', signed=True)

def command(ser : serial.Serial, op_code, data_bytes = b''):
    cmd_bytes = get_bytes(op_code, 1, signed=False) + data_bytes
    print(list(cmd_bytes))
    ser.write(cmd_bytes)
    wait()

def query_one(ser : serial.Serial, packet_id, read_size):
    command(ser, OP_QUERY_LIST, get_bytes(1, 1) + get_bytes(packet_id, 1))
    return ser.read(read_size)

def get_mode(ser : serial.Serial):
    mode_bytes = query_one(ser, PACKET_MODE, 1)
    mode = get_int(mode_bytes)
    print("mode:" + str(mode))
    return mode

def get_bump(ser : serial.Serial):
    packet_data = get_int(query_one(ser, PACKET_BUMPS, 1))
    print("bump:" + str(packet_data))
    if packet_data & Bump.Both == Bump.Both:
        return Bump.Both
    elif packet_data & Bump.Left == Bump.Left:
        return Bump.Left
    elif packet_data & Bump.Right == Bump.Right:
        return Bump.Right
    else:
        return Bump.Nope

def drive(ser : serial.Serial, velocity : int, radius : int, duration : float):
    drive_bytes = get_bytes(velocity, 2) + get_bytes(radius, 2)
    command(ser, OP_DRIVE, drive_bytes)
    wait(duration)

def stop(ser : serial.Serial):
    drive(ser, 0, 0, 0)

def back_up(ser : serial.Serial):
    drive(ser, -300, 32767, 0.5)

def turn_left_rand(ser : serial.Serial):
    drive(ser, randint(150, 300), Turn.CounterClockwise, rand(0.5, 2))

def turn_right_rand(ser : serial.Serial):
    drive(ser, randint(150, 300), Turn.Clockwise, rand(0.5, 2))

def express_pain(pains):
    pain = pains[randint(0, len(pains) - 1)]
    pygame.mixer.music.load(pain)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy() == True: # block program execution while pain is happening
        continue

def open_serial():
    return serial.Serial(port='/dev/ttyUSB0',baudrate=115200,timeout=1) # apparently this also open the port immediately

def main():
    pygame.mixer.init()
    pygame.mixer.music.set_volume(1.0)
    pains = glob.glob(AUDIO_DIR + '/*.mp3')

    ser = open_serial()

    try:
        print(ser)

        ser.rts = True
        wait(0.3)
        ser.rts = False

        command(ser, OP_START)
        wait(0.3)
        command(ser, OP_SAFE)
        wait(0.3)

        ser.reset_input_buffer()
        wait(0.3)

        mode = get_mode(ser)
        speed = 400
        while mode == MODE_SAFE:
            bump = get_bump(ser)
            if bump != Bump.Nope:
                stop(ser)
                express_pain(pains)
                back_up(ser)
                if bump == Bump.Right:
                    turn_left_rand(ser)
                elif bump == Bump.Left:
                    turn_right_rand(ser)
                else: # randomly turn right twice, because I am too lazy to figure out, how long I'd have to let roomba turn until it turns around 180 degrees xD
                    turn_right_rand(ser)
                    turn_right_rand(ser)
                # speed = randint(350, 500) # update speed after bump for a bit of randomness lol
            
            drive(ser, speed, 32767, 0)

            mode = get_mode(ser)
            
        print("Exiting program because mode is now " + str(mode))
    finally:
        ser.close()