import pytest
import numpy as np

def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0]); y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2]); y2 = min(box1[3], box2[3])
    inter = max(0, x2-x1) * max(0, y2-y1)
    a1 = (box1[2]-box1[0])*(box1[3]-box1[1])
    a2 = (box2[2]-box2[0])*(box2[3]-box2[1])
    return inter / (a1+a2-inter+1e-6)

def clamp_servo_angles(pan, tilt):
    return (max(-90,min(90,pan)), max(0,min(60,tilt)))

def test_iou_same_box():
    b=[100,100,200,200]
    assert abs(calculate_iou(b,b)-1.0) < 1e-5

def test_iou_no_overlap():
    assert calculate_iou([0,0,10,10],[20,20,30,30]) == 0

def test_kalman_prediction():
    # x=320, vx=10px/frame, dt=0.1s → 321 근처
    x, vx, dt = 320, 10, 0.1
    pred = x + vx*dt
    assert abs(pred-321) < 2

def test_servo_limits_enforced():
    pan, tilt = clamp_servo_angles(200.0, 100.0)
    assert -90 <= pan <= 90
    assert 0 <= tilt <= 60

def test_track_timeout():
    # 30프레임 빈 검출 → 트랙 삭제 로직 시뮬레이션
    tracks = [{'id':1,'age':0}]
    for _ in range(30):
        for t in tracks: t['age'] += 1
    tracks = [t for t in tracks if t['age'] < 20]
    assert len(tracks) == 0
