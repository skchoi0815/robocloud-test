from fusion_lite import distance_point_to_line, angle_diff

def test_point_on_line():
    assert distance_point_to_line([0,10],[0,0],0) < 1e-5

def test_angle_wrap():
    assert abs(angle_diff(10, 350) - 20) < 1e-5
    assert abs(angle_diff(350, 10) + 20) < 1e-5
