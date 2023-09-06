import sys
import cv2
import time
import threading

if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

class Camera:
    def __init__(self, resolution=(640, 480)):
        self.cap = None
        self.width = 640 # 分辨率
        self.height = 480
        self.frame = None
        self.opened = False
        self.th = threading.Thread(
            target=self.camera_task, args=(), daemon=True)
        self.th.start()

    def camera_open(self): # 开启摄像头
        try:
            self.cap = cv2.VideoCapture(-1) # 打开摄像头
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')) #分辨率为 MJPG 格式
            self.cap.set(cv2.CAP_PROP_FPS, 30) # 30帧
            #self.cap.set(cv2.CAP_PROP_SATURATION, 40)
            time.sleep(0.2)
            self.opened = True
        except Exception as e: # 是啥错误就报啥错误
            print(e)

    def camera_close(self):
        try:
            self.opened = False
            time.sleep(0.2)
            if self.cap is not None:
                self.cap.release()
            self.cap = None
        except Exception as e:
            print(e)

    def camera_task(self):
        print('cam')
        while True:
            try:
                if self.opened:
                    ret, frame_tmp = self.cap.read()
                    if ret:
                        self.frame = frame_tmp.copy()
                    else:
                        self.frame = None
                time.sleep(0.02)
            except Exception as e:
                time.sleep(0.05)

