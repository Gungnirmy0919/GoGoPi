#!/usr/bin/python32
# coding=utf8
import os
import sys
import cv2
import math
import time
import datetime
import threading
import numpy as np
import HiwonderSDK.Board as Board
import HiwonderSDK.Misc as Misc
from HiwonderSDK.PID import PID
import face_recognition

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

servo1_pid = PID(P=0.4, I=0.2, D=0.04)  # pid初始化 #上下
servo2_pid = PID(P=0.4, I=0.2, D=0.04)  # pid初始化 #左右
pitch_pid = PID(P=0.0005, I=0.001, D=0.001)
yaw_pid = PID(P=0.05, I=0.2, D=0.005)

servo1_pulse = 1850
servo2_pulse = 1500
pitch_speed = 0
yaw_speed = 0

conf_threshold = 0.3
modelFile = "/home/pi/GoGoPi/models/res10_300x300_ssd_iter_140000_fp16.caffemodel"
configFile = "/home/pi/GoGoPi/models/deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(configFile, modelFile)

#modelFile = "/home/pi/GoGoPi/models/opencv_face_detector_uint8.pb"
#configFile = "/home/pi/GoGoPi/models/opencv_face_detector.pbtxt"
#net = cv2.dnn.readNetFromTensorflow(modelFile, configFile)

isRunning = False
enableWheel = False

def reset():
    global isRunning, enableWheel
    global servo1_pulse, servo2_pulse
    global servo1_pid, servo2_pid
    global servo1_pulse, servo2_pulse
    global pitch_speed, yaw_speed

    print("FaceTracking Reset")
    isRunning = False
    enableWheel = False
    Board.setPWMServoPulse(1, servo1_pulse, 300)
    Board.setPWMServoPulse(2, servo2_pulse, 300)
    servo1_pid.clear()
    servo2_pid.clear()
    
def init():
    reset()

def exit():
    global isRunning, enableWheel
    isRunning = False
    enableWheel = False
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)

def start():
    global isRunning
    isRunning = True

def stop():
    global isRunning, enableWheel
    isRunning = False
    enableWheel= False
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)

#开启车声跟随
def setWheel(new_st):
    global enableWheel
    if new_st[0] > 0:
        enableWheel = True
    else:
        enableWheel = False
        Board.setMotor(1, 0)
        Board.setMotor(2, 0)
    return (True, ())

def run(img):
    global isRunning
    global servo1_pid, servo2_pid
    global servo1_pulse, servo2_pulse
    global pitch_speed, yaw_speed
    global yaw_pid, pitch_pid
    global net, conf_threshold

    if not isRunning:
        return img

    frame_resize = cv2.resize(img, (160, 120), interpolation=cv2.INTER_NEAREST)  #缩放画面降低运算量
    x_w = frame_resize.shape[:2][1]
    y_h = frame_resize.shape[:2][0]

    blob = cv2.dnn.blobFromImage(frame_resize, 0.5, (150, 150), [
                                 104, 117, 123], False, False)
    net.setInput(blob)
    detections = net.forward() #计算识别
    bboxes = []
    max_box = (0, 0, 0, 0, 0)
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > conf_threshold:
            #识别到的人了的各个坐标转换会未缩放前的坐标
            x1 = int(Misc.map((detections[0, 0, i, 3] * x_w), 0, x_w, 0, 640))
            y1 = int(Misc.map((detections[0, 0, i, 4] * y_h), 0, y_h, 0, 480))
            x2 = int(Misc.map((detections[0, 0, i, 5] * x_w), 0, x_w, 0, 640))
            y2 = int(Misc.map((detections[0, 0, i, 6] * y_h), 0, y_h, 0, 480))
            bboxes.append([x1, y1, x2, y2])
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2, 8) #将识别到的人脸框出
            tmp = (y2 - y1) * (x2 - x1)
            if tmp > max_box[0]: #判断是否时最大的人脸
                max_box = tmp, x1, y1, x2, y2

    img_center_x = 320
    img_center_y = 240
    if max_box[0] > 0:
        ########pid处理#########
        #以图像的中心点的x，y坐标作为设定的值，以当前x，y坐标作为输入#
        area, x1, y1, x2, y2 = max_box
        centerY = ((y2 - y1) / 2) + y1
        centerX = ((x2 - x1) / 2) + x1

        err = abs(img_center_y - centerY) #y轴偏差计算
        if err < 15:
            servo1_pid.SetPoint = centerY
        else:
            servo1_pid.SetPoint = img_center_y
        servo1_pid.update(centerY) #pid计算
        tmp = int(servo1_pulse + servo1_pid.output)
        tmp = 1000 if tmp < 1000 else tmp  #舵机角度限幅 
        servo1_pulse = 2500 if tmp > 2500 else tmp

        err = abs(img_center_x - centerX) #x轴偏差计算
        if err < 20:
            servo2_pid.SetPoint = 2 * img_center_x - centerX
        else:
            servo2_pid.SetPoint = img_center_x
        servo2_pid.update(2 * img_center_x - centerX) #pid计算
        tmp = int(servo2_pulse - servo2_pid.output)
        tmp = 500 if tmp < 500 else tmp
        servo2_pulse = 2500 if tmp > 2500 else tmp

        Board.setPWMServoPulse(1, servo1_pulse, 20) #设置舵机角度
        Board.setPWMServoPulse(2, servo2_pulse, 20)

        if 20000 < area < 40000:  # 据人脸所框的像素数通过控制小车前后运动
            pitch_pid.clear()
            pitch_pid.SetPoint = area
        else:
            pitch_pid.SetPoint = 30000
            pitch_pid.update(area)
        tmp = pitch_pid.output
        tmp = 100 if tmp > 100 else tmp
        tmp = -100 if tmp < -100 else tmp
        base_speed = tmp

        if 1400 < servo2_pulse < 1600:
            yaw_pid.clear()
            yaw_pid.SetPoint = servo2_pulse
        else:
            yaw_pid.SetPoint = 1500
        yaw_pid.update(servo2_pulse)
        tmp = yaw_pid.output
        tmp = 100 if tmp > 100 else tmp
        tmp = -100 if tmp < -100 else tmp
        direct_speed = tmp

        motor1 = base_speed + direct_speed
        motor1_direct = -1 if motor1 < 0 else 1

        motor2 = base_speed - direct_speed
        motor2_direct = -1 if motor2 < 0 else 1

        motor1 = Misc.map(abs(motor1), 0, 100, 30, 60)
        motor2 = Misc.map(abs(motor2), 0, 100, 30, 60)

        if enableWheel: #只有开启了车身跟随马达才会动
            Board.setMotor(1, int(motor1_direct * motor1))
            Board.setMotor(2, int(motor2_direct * motor2))
        else:
            yaw_pid.clear()
            pitch_pid.clear()
    else:
        yaw_pid.clear()
        Board.setMotor(1, 0)
        Board.setMotor(2, 0)
    return img