import sys
import time
import threading
import HiwonderSDK.Board as Board
import lab_adjust as lab_adjust
import RemoteControl as RemoteControl
import ColorTracking as ColorTracking
import FaceTracking as FaceTracking
import FingerDetect as FingerDetect
import Avoidance as Avoidance
from GoGoPi.Functions import LineTracking

RunningFunc = "" #当前运行中的玩法的序号
LastHeartbeat = 0 #最后一次心跳的时间戳
cam = None

#玩法的module与序号的字典

FUNCTIONS = {
    "1": RemoteControl,  # 遥控图传
    "2": ColorTracking,  # 颜色追踪
    "3": FaceTracking,  # 人脸追踪
    "4": FingerDetect,  # 手势识别
    "5": Avoidance,  # 自动避障(超声波)
    "6": LineTracking, # 循迹
    "9": lab_adjust
}

#心跳一次的调用
def doHeartbeat(tmp=()):
    global LastHeartbeat
    LastHeartbeat = time.time() + 7
    return (True, ())

#返回正在运动的玩法的run函数
def CurrentEXE():
    global RunningFunc
    return FUNCTIONS[RunningFunc]

#加载一个玩法
def loadFunc(newf):
    global RunningFunc
    new_func = int(newf[0])

    #Board.setMotor(1, 0)
    #Board.setMotor(2, 0)

    doHeartbeat()

    if new_func < 0 or new_func > 9:
        return (False,  sys._getframe().f_code.co_name + ": Invalid argument")
    else:
        try:
            if RunningFunc in FUNCTIONS:
                FUNCTIONS[RunningFunc].exit() #若当前由玩法正在运行则先退出当前玩法
            RunningFunc = str(new_func)
            cam.camera_close() #重新关开一次摄像头
            cam.camera_open()
            FUNCTIONS[RunningFunc].init() #调用新玩法的初始化
        except Exception as e:
            print(e)
    return (True, (new_func,))

#卸载玩法
def unloadFunc(tmp = ()):
    global RunningFunc 
    if RunningFunc in FUNCTIONS:
        #停止并退出当前玩法
        try:
            FUNCTIONS[RunningFunc].stop()
            FUNCTIONS[RunningFunc].exit()
        except Exception as e:
            print(e)
        RunningFunc = "" #将当前玩法设为0,即没有玩法
        print(RunningFunc)
    cam.camera_close() #关闭摄像头
    return (True, (0,))

def getLoadedFunc(newf):
    global RunningFunc
    return (True, (RunningFunc,))

#开始运行玩法， 玩法加载之后并不会执行追踪识别等操作，只是准备就绪，需要调用它的start函数启动运行
def startFunc(tmp = None):
    global RunningFunc
    print("START")
    FUNCTIONS[RunningFunc].start()
    return (True, (RunningFunc,))

#停止玩法的运行
def stopFunc(tmp = None):
    global RunningFunc
    print("STOP")
    FUNCTIONS[RunningFunc].stop()
    return (True, (RunningFunc,))

#手机APP心跳检查线程
DisableHeartbeat = False
def heartbeatTask():
    global LastHeartbeat
    global RunningFunc
    while True:
        try:
            if DisableHeartbeat == False:
                if LastHeartbeat < time.time():
                    if RunningFunc in FUNCTIONS:
                        unloadFunc()
            time.sleep(0.5)
        except KeyboardInterrupt:
            break

LastHeartbeat = time.time()
threading.Thread(target=heartbeatTask, daemon=True).start()
