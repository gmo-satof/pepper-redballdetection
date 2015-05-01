# -*- encoding: UTF-8 -*-

import argparse
import time
import math
from naoqi import ALProxy

def main(robotIP, PORT = 9559, filename = "redball.log"):

    f = open(filename)
    lines = f.readlines()
    f.close()


    names  = ["RShoulderPitch","RShoulderRoll","RElbowYaw","RElbowRoll"]
    angles = [[],[],[],[]]
    times = [[],[],[],[]]

    # 定数
    OFFSET_TIME   = 1.0  # 最初のポーズをとるまでの時間(s)
    L1            = 0.3  # 肩から肘までの距離(m)
    L2            = 0.3  # 肘から手までの距離(m)
    Z_SCALE       = 4.0  # RedBallの半径に対するZ軸方向距離の係数
    TIME_RATIO    = 1.0  # 再生時間の倍率
    MIN_DIRECTION = math.sqrt((L1 * L1) + (L2 * L2)) # RedBallまでの距離の最小値(肘の内角を90°までとした場合)
    MAX_DIRECTION = L1 + L2                          # RedBallまでの距離の最大値


    init_sec = 0.0   # 最初のポーズの時刻(s)
    pass_time = 0.0  # 最初のポーズからの経過時間(s)

    for line in lines:
        redball = eval(line.rstrip())

        time_sec = redball[0][0]
        time_mic = redball[0][1]
        center_x = redball[1][0]
        center_y = redball[1][1]
        size_x   = redball[1][2]
        size_y   = redball[1][3]

        last_time = pass_time

        if init_sec == 0.0:
            init_sec = time_sec

        pass_time = round( (time_sec - init_sec) + ( time_mic / 1000000.0 ) + OFFSET_TIME, 3 ) * TIME_RATIO

        # 経過時間が進んでいない場合はスキップ
        if last_time >= pass_time:
            continue

        # Redballの空間座標
        x = center_x
        y = center_y
        z = size_y * Z_SCALE

        # 原点からRedBallまでの空間直線距離
        d = math.sqrt( (x * x) + (y * y) + (z * z) )

        # d < math.sqrt((L1*L1) + (L2*L2)) の場合（肘の内角が90°以下になる場合）は、dとzを補正する
        if d < MIN_DIRECTION:
            d = MIN_DIRECTION
            z = math.sqrt( (d * d) - (x * x) - (y * y) )
        # d > L1 + L2 の場合も補正
        if d > MAX_DIRECTION:
            d = L1 + L2
            zp2 = (d * d) - (x * x) - (y * y)
            if zp2 < 0:
                z = 0
            else:
                z = math.sqrt( zp2)

        # 肘の空間座標と角度（dの半分を初期値としている）
        x1 = (L1 + L2) * L1 / x if x != 0 else 0.0
        y1 = (L1 + L2) * L1 / y if y != 0 else 0.0
        z1 = (L1 + L2) * L1 / z if z != 0 else 0.0
        q2 = 0.0

        # 肘の回転が必要な場合、逆運動学により肘の座標および角度を求める
        if d < L1 + L2:
            # 空間座標における原点からRedBallまでの線分を含む垂直平面P上のRedBall座標(px2,py2)
            px2 = math.sqrt((d * d) - (y * y))
            py2 = y * (-1)  # y軸反転のため

            # 垂直平面上の原点(0,0)、肘座標(x1,y1)、RedBall座標(x2,y2)における
            # 原点-肘-RedBallの内角a
            a = math.acos( ( (L2 * L2) + (L1 * L1) - ( (px2 * px2) + (py2 * py2) ) ) / ( 2 * L1 * L2 ) )
            # 肘-原点-RedBallの内角b
            b = math.acos( ( (px2 * px2) + (py2 * py2) - (L2 * L2) + (L1 * L1) ) / ( 2 * L1 * math.sqrt( (px2 * px2) + (py2 * py2) ) ) )

            # L1の角度
            q1 = math.atan(py2 / px2) - b
            # L2の角度(L1からの相対角度)
            q2 = math.pi - a

            # 平面上の肘の座標
            px1 = math.cos(q1) * L1
            py1 = math.sin(q1) * L1

            # 肘の平面上の座標から空間座標のx, zに変換
            x1 = (x * px1) / px2 if px2 != 0 else 0  # x : x1 = px2 : px1
            y1 = py1 * (-1)                           # y軸反転のため
            z1 = (z * px1) / px2 if px2 != 0 else 0  # z : z1 = px2 : px1

        # ShoulderPitch
        shoulder_pitch = math.atan(y1 / z1) if z1 != 0 else 0
        angles[0].append(shoulder_pitch)
        times[0].append(pass_time)
        # ShoulderRoll
        shoulder_roll = math.atan(x1 / math.sqrt((y1 * y1) + (z1 * z1))) * (-1.000)   # 左右フリップのため
        angles[1].append(shoulder_roll)
        times[1].append(pass_time)
        # ElbowYaw
        elbow_yaw = shoulder_pitch + (math.pi / 2)
        angles[2].append(elbow_yaw)
        times[2].append(pass_time)
        # ElbowRoll
        elbow_roll = q2
        angles[3].append(elbow_roll)
        times[3].append(pass_time)

    isAbsolute  = True

    print names
    print angles
    print times

    motionProxy = ALProxy("ALMotion", robotIP, PORT)
    for name in ["RShoulder", "RElbow", "RWrist"]:
        motionProxy.setStiffnesses(name, 1.0)

    motionProxy.angleInterpolation(names, angles, times, isAbsolute)

    for name in ["RShoulder", "RElbow", "RWrist"]:
        motionProxy.setStiffnesses(name, 0.0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot ip address")
    parser.add_argument("--port", type=int, default=9559,
                        help="Robot port number")
    parser.add_argument("--filename", type=str, default="redball.log",
                        help="RedBallDetected file")
    args = parser.parse_args()
    main(args.ip, args.port, args.filename)
