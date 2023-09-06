#!/usr/bin/python32
# coding=utf8
import os
import sys
import cv2
import math
import time
import datetime
import threading
import yaml_handle
import numpy as np
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
from HiwonderSDK.PID import PID

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

# 对每个颜色的 rgb 值进行定义
range_rgb = {
    'red': (255, 0, 255),
    'blue': (255, 255,),
    'green': (0, 255, 255),
    'black': (0, 0, 0),
}

isRunning = False
servo1_pid = PID(P=0.6, I=0.5, D=0.08)  # pid初始化 #上下
servo2_pid = PID(P=0.5, I=0.35, D=0.065)  # pid初始化 #左右
pitch_pid = PID(P=0.17, I=0.08, D=0.015) #车身前后
pitch_pid1 = PID(P=2, I=0.5, D=0.20)
yaw_pid = PID(P=0.07, I=0.03, D=0.008) #车身前后
#yaw_pid = PID(P=0.0, I=0.0, D=0.00)
#pitch_pid = PID(P=0.12, I=0.06, D=0.03)
#pitch_pid1 = PID(P=2, I=1.0, D=0.15)
#yaw_pid = PID(P=0.04, I=0.015, D=0.003)

servo1_pulse = 1500 #使得舵机位置在正中间
servo2_pulse = 1500
pitch_speed = 0
yaw_speed = 0
target_color = ""

lab_data = None
def load_config():
    global lab_data
    
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path) #读取配置文件

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

#设置扩展板的RGB灯颜色使其跟要追踪的颜色一致
def set_rgb(color):
    if color == "red":
        Board.RGB.setPixelColor(0, Board.PixelColor(255, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(255, 0, 0))
        Board.RGB.show()
    elif color == "green":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 255, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 255, 0))
        Board.RGB.show()
    elif color == "blue":
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 255))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 255))
        Board.RGB.show()
    else:
        Board.RGB.setPixelColor(0, Board.PixelColor(0, 0, 0))
        Board.RGB.setPixelColor(1, Board.PixelColor(0, 0, 0))
        Board.RGB.show()

#重置
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

#设置目标颜色
def setTargetColor(target_color_new = ('red', )):
    global target_color
    target_color = target_color_new[0]
    set_rgb(target_color)
    return (True, ())

#退出玩法
def exit():
    global isRunning
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)
    target_color = ""
    set_rgb(target_color)
    isRunning = False

#初始化
def init():
    load_config()
    reset()

def start():
    global isRunning
    isRunning = True

def stop():
    global isRunning, target_color
    target_color = ""
    set_rgb(target_color)
    isRunning = False
    Board.setMotor(1, 0)
    Board.setMotor(2, 0)

#玩法主操作
def run(img): #参数是一个图片，然后定义一大堆全局变量
    global isRunning
    global target_color
    global servo1_pid, servo2_pid
    global servo1_pulse, servo2_pulse
    global pitch_speed, yaw_speed
    global yaw_pid, pitch_pid

    if not isRunning:
        return img

    if target_color == "":
        return img

    frame_resize = cv2.resize(img, (320, 240), interpolation=cv2.INTER_NEAREST)
    img_center_x = frame_resize.shape[:2][1]/2  # 获取缩小图像的宽度值的一半
    img_center_y = frame_resize.shape[:2][0]/2

    frame_lab = cv2.cvtColor(frame_resize, cv2.COLOR_BGR2LAB)  # 将图像转换到LAB空间
    frame_mask = cv2.inRange(frame_lab,
                             (lab_data[target_color]['min'][0],
                              lab_data[target_color]['min'][1],
                              lab_data[target_color]['min'][2]),
                             (lab_data[target_color]['max'][0],
                              lab_data[target_color]['max'][1],
                              lab_data[target_color]['max'][2]))  #对原图像和掩模进行位运算    

    opened = cv2.morphologyEx(frame_mask, cv2.MORPH_OPEN, np.ones((6, 6), np.uint8))  # 开运算
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE,np.ones((6, 6), np.uint8))  # 闭运算
    contours = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]  # 找出所有外轮廓

    areaMaxContour = getAreaMaxContour(contours)  # 找到最大的轮廓

    if areaMaxContour is not None:  # 有找到最大面积
        (centerX, centerY), radius = cv2.minEnclosingCircle(
            areaMaxContour)  # 获取最小外接圆
        if radius >= 3:

            ########pid处理#########
            #以图像的中心点的x，y坐标作为设定的值，以当前x，y坐标作为输入#

            err = abs(img_center_y + 20 - centerY) #计算y轴误差，+20使目标位置处于中心偏下位置
            if err < 30:
                servo1_pid.SetPoint = centerY #误差范围内
            else:
                servo1_pid.SetPoint = img_center_y + 20 

            servo1_pid.update(centerY) #更新pid
            tmp = int(servo1_pulse + servo1_pid.output)
            tmp = 950 if tmp < 950 else tmp #舵机角度限幅
            servo1_pulse = 2000 if tmp > 2000 else tmp

            err = abs(img_center_x - centerX) #计算x轴误差
            if err < 40:
                servo2_pid.SetPoint = 2 * img_center_x - centerX # ‘2*'将左右对应数值反转
            else:
                servo2_pid.SetPoint = img_center_x

            servo2_pid.update(2 * img_center_x - centerX) #更新pid
            tmp = int(servo2_pulse - servo2_pid.output) 
            tmp = 500 if tmp < 500 else tmp #限幅
            servo2_pulse = 2500 if tmp > 2500 else tmp

            Board.setPWMServoPulse(1, servo1_pulse, 20)  #控制舵机运动
            Board.setPWMServoPulse(2, servo2_pulse, 20)

            tmp = 0
            #当舵机位置小于1300时，车身的前后运动由云台的俯仰角驱动
            #当舵机位置大于等于1300时，车声的前后运动由画面中色块的最小外接圆半径驱动
            if servo1_pulse < 1300:
                if  1050 < servo1_pulse < 1200:
                    pitch_pid.SetPoint = servo1_pulse
                else:
                    pitch_pid.SetPoint = 1100
                pitch_pid.update(servo1_pulse)
                tmp = pitch_pid.output
            else:
                pitch_pid.clear()
                pitch_pid.SetPoint = servo1_pulse
                if 25 < radius < 45:
                    pitch_pid1.SetPoint = radius
                else:
                    pitch_pid1.SetPoint = 30

                if radius > 50: #半径太大时会后退太快，做一个限幅
                    pitch_pid1.update(50)
                else:
                    pitch_pid1.update(radius)
                tmp = -pitch_pid1.output

            tmp = 100 if tmp > 100 else tmp
            tmp = -100 if tmp < -100 else tmp
            base_speed = -tmp
           
            #车声转向由云台z轴偏转来驱动
            if 1350 < servo2_pulse < 1650:
                yaw_pid.clear()
                yaw_pid.SetPoint = servo2_pulse
            else:
                yaw_pid.SetPoint = 1500

            yaw_pid.update(servo2_pulse)
            tmp = yaw_pid.output
            tmp = 45 if tmp > 45 else tmp #限幅，车身转向太快摄像头跟不上
            tmp = -45 if tmp < -45 else tmp
            direct_speed = tmp

            motor1 = base_speed + direct_speed
            motor1_direct = -1 if motor1 < 0 else 1

            motor2 = base_speed - direct_speed
            motor2_direct = -1 if motor2 < 0 else 1

            motor1 = Misc.map(abs(motor1), 0, 100, 30, 70) #马达在0～30的区间扭矩不够，动不了，做个映射
            motor2 = Misc.map(abs(motor2), 0, 100, 30, 70)
            
            motor1 = int(motor1_direct * motor1)
            motor2 = int(motor2_direct * motor2)

            if -35 < motor1 < 35:
                motor1 = 0
            if -35 < motor2 < 35:
                motor2 = 0
            Board.setMotor(1, motor1) #设置马达速度
            Board.setMotor(2, motor2)

            centerX = int(Misc.map(centerX, 0, 320, 0, 640))
            centerY = int(Misc.map(centerY, 0, 240, 0, 480))
            radius = int(Misc.map(radius, 0, 320, 0, 640))

            #画面上画出正在追踪的色块
            cv2.circle(img, (int(centerX), int(centerY)),
                       int(radius), range_rgb[target_color], 2)
    else:
        pass
        Board.setMotor(1, 0)
        Board.setMotor(2, 0)

    return img #返回画面
