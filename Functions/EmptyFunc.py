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

from GoGoPi import yaml_handle
from GoGoPi.HiwonderSDK import Board
from GoGoPi.HiwonderSDK.PID import PID

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

isRunning = False
servo1_pid = PID(P=0.6, I=0.5, D=0.08)  # pid初始化 #上下
servo2_pid = PID(P=0.5, I=0.35, D=0.065)  # pid初始化 #左右
pitch_pid = PID(P=0.17, I=0.08, D=0.015) #车身前后
pitch_pid1 = PID(P=2, I=0.5, D=0.20)
yaw_pid = PID(P=0.07, I=0.03, D=0.008) #车身前后

servo1_pulse = 1500 #使得舵机位置在正中间
servo2_pulse = 1500
pitch_speed = 0
yaw_speed = 0
target_color = "black"

lab_data = None


def load_config():
    global lab_data

    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)  # 读取配置文件


load_config()

# 找出面积最大的轮廓
# 参数为要比较的轮廓的列表
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours:  # 历遍所有轮廓
        contour_area_temp = math.fabs(cv2.contourArea(c))  # 计算轮廓面积
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp > 20:  # 只有在面积大于20，最大面积的轮廓才是有效的，以过滤干扰
                area_max_contour = c
    return area_max_contour  # 返回最大的轮廓

def set_rgb(color):
    Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
    Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
    Board.RGB.show()


def reset():
    global target_color
    global servo1_pulse, servo2_pulse
    global servo1_pid, servo2_pid
    global servo1_pulse, servo2_pulse
    global pitch_speed, yaw_speed

    print("ColorTracking Reset")
    servo1_pulse = 1100
    servo2_pulse = 1500

    Board.setPWMServoPulse(1, servo1_pulse, 300)
    Board.setPWMServoPulse(2, servo2_pulse, 300)
    servo1_pid.clear()
    servo2_pid.clear()
    target_color = ""
    set_rgb(target_color)
    return None


def init():
    load_config()
    reset()
    return None


def exit():
    global isRunning
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    target_color = ""
    set_rgb(target_color)
    isRunning = False
    return None


def run(img):
    return img
