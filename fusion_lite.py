import numpy as np

def distance_point_to_line(point, origin, bearing_deg):
    theta = np.radians(bearing_deg)
    d = np.array([np.sin(theta), np.cos(theta)])
    v = np.array(point) - np.array(origin)
    perp = v - d * np.dot(v, d)
    return float(np.linalg.norm(perp))

def angle_diff(a_deg, b_deg):
    return (a_deg - b_deg + 180.0) % 360.0 - 180.0
