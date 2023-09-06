#!/usr/bin/python3
#coding=utf8
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
Threshold = 20.0
TextColor = (255,255,0)
TextSize = 12

__isRunning = False
__until = 0
dist = 0

def reset():
    pass

#进入玩法初始化
def init():
    global Threshold
    Board.setPWMServoPulse(1, 1300, 500)
    Board.setPWMServoPulse(2, 1500, 500)
    Threshold = 20.0

#退出玩法
def exit():
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    HWSONAR.setRGBMode(0)
    HWSONAR.setPixelColor(0, Board.PixelColor(0,0,0))
    HWSONAR.setPixelColor(1, Board.PixelColor(0,0,0))

#设置阈值调用
def setThreshold(args):
    global Threshold
    Threshold = args[0]
    return (True, (Threshold,))

def getThreshold(args):
    global Threshold
    return (True, (Threshold,))

def start():
    global __isRunning
    __isRunning = True


def stop():
    global __isRunning
    __isRunning = False
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)


#主操作
def run(img):
    global __isRunning
    global HWSONAR
    global Threshold
    global __until, dist
    t = time.time()
    dist = HWSONAR.getDistance() / 10.0 #获取距离

    if __isRunning:
        if t >= __until: 
            if dist < Threshold: #判断距离
                Board.setMotor(1, -40)
                Board.setMotor(2, 40)
                __until = time.time() + 0.3
            else:
                Board.setMotor(1, 40)
                Board.setMotor(2, 40)

    return cv2.putText(img, "Dist:%.1fcm"%dist, (30,480-30), cv2.FONT_HERSHEY_SIMPLEX, 1.2, TextColor, 2)  #将距离写在图片上并返回图片


