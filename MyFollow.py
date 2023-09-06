import os
import sys
import cv2
import math
import time
import datetime
import threading
import yaml_handle
import numpy as np
import HiwonderSDK.Sonar
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
from HiwonderSDK.PID import PID
import RPi.GPIO as GPIO

sonar=HiwonderSDK.Sonar.Sonar()
video_capture = cv2.VideoCapture(-1)  # 打开摄像头
#video_capture.set(3,160) # 设置窗口大小，太大运算慢
#video_capture.set(4,120)

Board.setPWMServoPulse(1,1500,100)
Board.setPWMServoPulse(2,1500,100)
video_capture.set(3,640) # 设置窗口大小，太大运算慢
video_capture.set(4,480)

print("将任何物体放于车前以启动循迹")

while sonar.getDistance() > 200:
    time.sleep(1)

print("循迹系统启动中")

Board.setPWMServoPulse(1,900,100)
Board.setPWMServoPulse(2,1500,100)
#time.sleep(3)
noSignal=True
# 树莓派小车运动函数
def t_up():
    Board.setMotor(1, 100)
    Board.setMotor(2, 100)
    time.sleep(0)

def t_stop():
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    time.sleep(0)

def t_down():
    Board.setMotor(1, -30)
    Board.setMotor(2, -30)
    time.sleep(0)


def t_left():
    Board.setMotor(1, 30)
    Board.setMotor(2, 100)
    time.sleep(0)

def t_right():
    Board.setMotor(1, 100)
    Board.setMotor(2,30)
    time.sleep(0)

# def begin(m):
#     global noSignal
#     while (noSignal):
#         m = []
#         for i in range()
#         if m.all == 0:
#             print("识别到了")
#             noSignal=False
#             break
#         print("用手遮挡摄像头以开始循迹")
#         time.sleep(0.05)
#出发信号：手势识别or超声识别
        
        
t_stop()
time.sleep(8)

while 1:
    #begin()
    print("5秒后出发！！！")
    #time.sleep(5)

    # Capture the frames
    ret, frame = video_capture.read()
    # Crop the image　
    #crop_img = frame[60:120, 0:160]！
    crop_img = frame[0:480, 0:640]
    # Convert to grayscale 二值图像处理，灰度化
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    # Gaussian blur  高斯模糊:减少图像噪声以及降低细节层次
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    '''
     # Color thresholding 阈值处理
     src：表示的是图片源
     thresh：表示的是是阈值（起始值）
     maxval：表示的是最大值
     type：表示的是这里划分的时候使用的什么类型的算法**，常用值为0（cv2.THRESH_BINARY）**
    '''
    ret, thresh1 = cv2.threshold(blur, 85, 255, cv2.THRESH_BINARY_INV)
    stopline1 = []
    stopline2 = []
    stopline3 = []
    
    for i in range(0,640):
        stopline1.append(thresh1[100][i])
        stopline1.append(thresh1[101][i])
        stopline1.append(thresh1[102][i])
        stopline1.append(thresh1[103][i])
        stopline1.append(thresh1[104][i])
        stopline1.append(thresh1[105][i])

        stopline2.append(thresh1[200][i])
        stopline2.append(thresh1[201][i])
        stopline2.append(thresh1[202][i])
        stopline2.append(thresh1[203][i])
        stopline2.append(thresh1[204][i])
        stopline2.append(thresh1[205][i])

        stopline3.append(thresh1[300][i])
        stopline3.append(thresh1[301][i])
        stopline3.append(thresh1[302][i])
        stopline3.append(thresh1[303][i])
        stopline3.append(thresh1[304][i])
        stopline3.append(thresh1[305][i])
    
    print(sum(stopline1))
    print(sum(stopline2))
    print(sum(stopline3))
    if sum(stopline1) > 300000 or sum(stopline2) >300000 or sum(stopline3) > 300000:
        Board.setMotor(1,40)
        Board.setMotor(2,40)
        time.sleep(1)
        Board.setMotor(1,0)
        Board.setMotor(2,0)
        exit()

    #ret, thresh1 = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY)
    #ret, thresh1 = cv2.threshold(blur, 80, 255, cv2.THRESH_BINARY)
    # Erode and dilate to remove accidental line detections
    # 形态学处理 消除噪音
    mask = cv2.erode(thresh1, None, iterations=2)  # 腐蚀
    mask = cv2.dilate(mask, None, iterations=2)  # 膨胀

    # Find the contours of the frame　寻找所有轮廓
    contours, hierarchy = cv2.findContours(mask.copy(), 1, cv2.CHAIN_APPROX_NONE)
    # Find the biggest contour (if detected)　最大轮廓
    if len(contours) > 0:
        c = max(contours, key=cv2.contourArea)  # cv2.contourArea轮廓面积
        M = cv2.moments(c)  # cv2.moments()是用于计算图像矩，然后通过图像矩计算质心
        # 求轮廓的中心位置
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])

        #print("中心是：(%d,%d)"%(cx,cy))
        '''
        cv2.line(plot,(0,y),(int(h * mul),y),(255,0,0),w)
        第一个参数 img：要划的线所在的图像;
        第二个参数 pt1：直线起点
        第三个参数 pt2：直线终点
        第四个参数 color：直线的颜色 
        第五个参数 thickness=1：线条粗细
        '''
        # 过质心的两条线
        #cv2.line(crop_img, (cx, 0), (cx, 720), (255, 0, 0), 1)
        #cv2.line(crop_img, (0, cy), (1280, cy), (255, 0, 0), 1)
        #cv2.line(crop_img,(0,100),(640,100),(0,0,255), 1)
        #cv2.line(crop_img,(0,103),(640,103),(0,0,255), 1)

        cv2.drawContours(crop_img, contours, -1, (0, 255, 0), 1)
        # 偏右 朝左边
        #if cx >= 120:！
        if cx >= 416:
            t_right()
            #print("Turn Right!")
        # 50-120范围一直前进
        #if cx < 120 and cx > 50:！
        if cx < 416 and cx > 223:
            t_up()
            #print("On Track!")
        if cx <= 223:
            # 偏左，向右
            t_left()
            #print("Turn Left")
   
    else:
        print("I don't see the line")
        # Display the resulting frame
    #cv2.imshow('frame', crop_img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        Board.setMotor(1, 0)
        Board.setMotor(2, 0)
        GPIO.cleanup()
        break









