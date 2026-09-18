from vision_pipeline import should_enhance, fuse_detections, calculate_iou, estimate_pipeline_ms, can_run_full_pipeline

def test_high_conf_track():
    assert should_enhance(0.96) == 'track'

def test_uncertain_enhance():
    assert should_enhance(0.73) == 'enhance'  # 8픽셀 blob 케이스

def test_low_ignore():
    assert should_enhance(0.3) == 'ignore'

def test_fuse_both():
    t = [{'bbox': [100,100,50,50], 'confidence': 0.8}]
    v = [{'bbox': [105,105,50,50], 'confidence': 0.9}]
    f = fuse_detections(t, v)
    assert len(f) == 1
    assert f[0]['source'] == 'both'
    assert abs(f[0]['combined_conf'] - 0.85) < 1e-5

def test_fuse_thermal_only():
    t = [{'bbox': [100,100,50,50], 'confidence': 0.8}]
    v = [{'bbox': [300,300,50,50], 'confidence': 0.9}]
    f = fuse_detections(t, v)
    assert len(f) == 2

def test_performance_budget():
    # YOLO만이면 33ms → 30 FPS
    assert estimate_pipeline_ms([{'confidence': 0.95}]) < 60
    # uncertain 1개면 33+45+215=293ms → 3.2 FPS, 그래도 돌릴 수 있음
    assert can_run_full_pipeline([{'confidence': 0.73}]) is True
