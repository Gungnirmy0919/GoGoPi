import sys
sys.path.append("..")
from GoGoPi.HiwonderSDK import Board

if sys.version_info.major != 3: # 必须使用 python3以上版本运行
    print('Please run this program with python3!')
    sys.exit(0)

import os
if os.geteuid() != 0: # 运行权限必须为root
    print('This program must be run as root!')
    sys.exit(0)

Board.setPWMServoAngle(1,90)
Board.setPWMServoAngle(2,90)

