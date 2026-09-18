from vision_3d import estimate_distance_m, predict_next_box
import pytest

def test_farther_when_smaller():
    near = estimate_distance_m(40)  # 0.35*800/40 = 7m
    far = estimate_distance_m(8)    # 0.35*800/8 = 35m
    assert far > near
    assert 30 < far < 40
    assert abs(estimate_distance_m(20, focal_px=800, real_width_m=0.35) - 14.0) < 1e-5

def test_invalid_pixel():
    with pytest.raises(ValueError):
        estimate_distance_m(0)

def test_flow_prediction():
    box = [100, 100, 50, 50]
    pred = predict_next_box(box, [10, 5], dt=0.1)
    assert abs(pred[0] - 101) < 1e-5
    assert abs(pred[1] - 100.5) < 1e-5
