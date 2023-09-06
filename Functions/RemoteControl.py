#!/usr/bin/python3
# coding=utf8
import os
import sys
import cv2
import math
import time
import datetime
import threading
import queue
import HiwonderSDK.Board as Board

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

HWSONAR = None


def reset():
    Board.setPWMServoPulse(1, 1500, 300)
    Board.setPWMServoPulse(2, 1500, 300)
    return None



def exit():
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)

def start():
    print("RemoteControl reset")
    return reset()

def init():
    start()
    return None


def stop():
    pass

def run(img):
    return img
