# Ch22 - Monocular distance + optical flow prediction

def estimate_distance_m(pixel_width: float, focal_px: float = 800.0, real_width_m: float = 0.35) -> float:
    # pixel 작을수록 멀다. 20px ≈ 91m (60도 FOV 카메라 예시)
    if pixel_width <= 0:
        raise ValueError("pixel_width must be > 0")
    return (real_width_m * focal_px) / pixel_width

def predict_next_box(box, velocity, dt: float = 0.1):
    # box [x,y,w,h], velocity [vx,vy] px/s
    x, y, w, h = box
    vx, vy = velocity
    return [x + vx*dt, y + vy*dt, w, h]
